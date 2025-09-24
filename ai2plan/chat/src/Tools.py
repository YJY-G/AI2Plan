from typing import Optional
import os
import time
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_deepseek import ChatDeepSeek
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

from .Memory import MemoryClass
from langchain_core.output_parsers import PydanticOutputParser
import contextvars
from django.utils import timezone
import json
from decimal import Decimal, InvalidOperation

# === 会话与用户上下文 ===
CURRENT_SESSION_ID = contextvars.ContextVar("CURRENT_SESSION_ID", default="")
CURRENT_USER_ID = contextvars.ContextVar("CURRENT_USER_ID", default=None)

def set_current_session_id(value:Optional[str])->None:
    CURRENT_SESSION_ID.set(value)

def set_current_user_id(value)->None:
    CURRENT_USER_ID.set(value)

# === 业务模型 ===
from users.models import User
from todo.models import Todo
from accounting.models import Account, Category, Transaction
from datetime import datetime, timedelta

# === Pydantic 入参与输出模型 ===
class CreateTodoInput(BaseModel):
    title: str = Field(..., description="待办标题，必须，简短精确")
    description: Optional[str] = Field("", description="待办描述，可选")
    due_date: Optional[str] = Field(
        None,
        description="截止时间。支持 YYYY-MM-DD、YYYY-MM-DD HH:MM、YYYY-MM-DDTHH:MM:SS"
    )

class CreateTransactionInput(BaseModel):
    date: str = Field(..., description="交易日期，格式 YYYY-MM-DD")
    amount: float = Field(..., gt=0, description="金额，正数")
    transaction_type: str = Field(..., pattern="^(income|expense)$", description="仅支持 income 或 expense")
    category_name: str = Field(..., description="分类名，如 餐饮/交通/工资")
    account_name: str = Field(..., description="账户名，如 现金/银行卡/微信/支付宝")
    description: Optional[str] = Field("", description="备注，可选")

class ToolResult(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="对本次操作的简短说明")
    data: Optional[dict] = Field(None, description="可选的结构化数据载荷")

# 提供输出解析器（供提示词中参考格式）
TOOL_RESULT_PARSER = PydanticOutputParser(pydantic_object=ToolResult)

# 配置管理
class Config:
    def __init__(self):
        load_dotenv()
        self.setup_environment()
        
    @staticmethod
    def setup_environment():
        required_vars = [
            "SERPAPI_API_KEY",
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_API_BASE",
        ]
        for var in required_vars:
            if not os.getenv(var):
                raise EnvironmentError(f"Missing required environment variable: {var}")
        os.environ.update({
            "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY"),
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
            "DEEPSEEK_API_BASE": os.getenv("DEEPSEEK_API_BASE")
        })

# 工具函数
@tool
def search(query: str) -> str:
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具."""
    serp = SerpAPIWrapper()
    return serp.run(query)

@tool(parse_docstring=True)
def get_info_from_local(query: str,session_id: Optional[str] = None) -> str:
    """从本地知识库获取信息。

    Args:
        query (str): 用户的查询问题
        session_id (Optional[str]): 会话ID(可选，默认从上下文注入)

    Returns:
        str: 从知识库中检索到的答案
    """
    session_id = session_id or CURRENT_SESSION_ID.get()
    llm = ChatDeepSeek(model=os.getenv("DEEPSEEK_MODEL_NAME"),api_key=os.getenv("DEEPSEEK_API_KEY"),api_base=os.getenv("DEEPSEEK_API_BASE"))
    memory = MemoryClass(memorykey=os.getenv("MEMORY_KEY"),model=os.getenv("DEEPSEEK_MODEL_NAME"))
    chat_history = memory.get_memory(session_id=session_id).messages if session_id else []
    
    condense_question_prompt = ChatPromptTemplate.from_messages([
        ("system", "给出聊天记录和最新的用户问题。可能会引用聊天记录中的上下文，提出一个可以理解的独立问题。没有聊天记录，请勿回答。必要时重新配制，否则原样退还。"),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    client = QdrantClient(path=os.getenv("PERSIST_DIR","./vector_store"))
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name=os.getenv("EMBEDDING_COLLECTION"), 
        embedding=HuggingFaceEmbeddings(
            model=os.getenv("EMBEDDING_MODEL"),
        )
    )
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 10}
    )
    qa_chain = create_retrieval_chain(
        create_history_aware_retriever(llm, retriever, condense_question_prompt),
        create_stuff_documents_chain(
            llm,
            ChatPromptTemplate.from_messages([
                ("system", "你是回答问题的助手。使用下列检索到的上下文回答。这个问题。如果你不知道答案，就说你不知道。最多使用三句话，并保持回答简明扼要。\n\n{context}"),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])
        )
    )
    res = qa_chain.invoke({
        "input": query,
        "chat_history": chat_history,
    })
    return res["answer"]

# 待办：使用 Pydantic 约束入参，并以 JSON 返回
@tool("create_todo", args_schema=CreateTodoInput)
def create_todo(title: str, description: Optional[str] = "", due_date: Optional[str] = None) -> str:
    """创建一个属于当前登录用户的待办事项。当用户表达待办需求时调用。"""
    try:
        user_id = CURRENT_USER_ID.get()
        if not user_id:
            return json.dumps(ToolResult(success=False, message="未检测到用户上下文").model_dump(), ensure_ascii=False)

        try:
            user = User.objects.get(userid=user_id)
        except User.DoesNotExist:
            return json.dumps(ToolResult(success=False, message="用户不存在").model_dump(), ensure_ascii=False)

        dt = None
        if due_date:
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed = datetime.strptime(due_date, fmt)
                    if fmt == "%Y-%m-%d":
                        parsed = parsed + timedelta(hours=23, minutes=59)
                    if timezone.is_naive(parsed):
                        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                    dt = parsed
                    break
                except ValueError:
                    continue

        # 解析完成后，增加校验
        if dt is not None and dt < timezone.now():
            return json.dumps(ToolResult(success=False, message="截止时间早于当前时间，请确认是否需要设置为未来时间").model_dump(), ensure_ascii=False)

        todo = Todo.objects.create(
            user=user,
            title=title.strip()[:255],
            description=(description or "").strip(),
            due_date=dt
        )
        return json.dumps(ToolResult(
            success=True,
            message=f"已创建待办：{todo.title}",
            data={"id": todo.id, "title": todo.title}
        ).model_dump(), ensure_ascii=False)
    except Exception as e:
        return json.dumps(ToolResult(success=False, message=f"创建失败：{str(e)}").model_dump(), ensure_ascii=False)

# 记账：使用 Pydantic 约束入参，并以 JSON 返回
@tool("create_transaction", args_schema=CreateTransactionInput)
def create_transaction(date: str, amount: float, transaction_type: str, category_name: str, account_name: str, description: Optional[str] = "") -> str:
    """创建一条属于当前登录用户的记账记录。"""
    user_id = CURRENT_USER_ID.get()
    if not user_id:
        return json.dumps(ToolResult(success=False, message="未检测到用户上下文").model_dump(), ensure_ascii=False)

    try:
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        return json.dumps(ToolResult(success=False, message="用户不存在").model_dump(), ensure_ascii=False)

    try:
        tx_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return json.dumps(ToolResult(success=False, message="日期格式应为 YYYY-MM-DD").model_dump(), ensure_ascii=False)

    # 金额与类型
    try:
        amt_dec = Decimal(str(amount))
        if amt_dec <= Decimal("0"):
            return json.dumps(ToolResult(success=False, message="金额必须为正数").model_dump(), ensure_ascii=False)
    except (InvalidOperation, Exception):
        return json.dumps(ToolResult(success=False, message="金额格式不正确").model_dump(), ensure_ascii=False)

    ttype = transaction_type.lower().strip()
    if ttype not in ("income", "expense"):
        return json.dumps(ToolResult(success=False, message="transaction_type 仅支持 'income' 或 'expense'").model_dump(), ensure_ascii=False)

    cat_name = category_name.strip()[:100]
    acc_name = account_name.strip()[:100]

    # 分类与账户（若不存在则创建）
    category, _ = Category.objects.get_or_create(
        user=user, name=cat_name,
        defaults={"type": ttype, "description": ""}
    )
    account, _ = Account.objects.get_or_create(
        user=user, name=acc_name,
        defaults={"balance": Decimal("0"), "description": ""}
    )

    # 创建交易（金额用 Decimal）
    tx = Transaction.objects.create(
        user=user,
        date=tx_date,
        amount=amt_dec,
        description=(description or "").strip(),
        category=category,
        account=account,
        transaction_type=ttype
    )

    # 即时同步账户余额（全用 Decimal）
    current_balance = account.balance or Decimal("0")
    if ttype == "income":
        account.balance = current_balance + amt_dec
    else:
        account.balance = current_balance - amt_dec
    account.save(update_fields=["balance"])

    return json.dumps(ToolResult(
        success=True,
        message=f"已记录{ '收入' if ttype=='income' else '支出' } {amt_dec} 元",
        data={
            "id": tx.id,
            "date": str(tx.date),
            "amount": str(tx.amount),
            "transaction_type": tx.transaction_type,
            "category": category.name,
            "account": account.name,
            "balance_after": str(account.balance)
        }
    ).model_dump(), ensure_ascii=False)