from langchain.agents import AgentExecutor,create_tool_calling_agent,create_structured_chat_agent
from langchain_deepseek import ChatDeepSeek
from langchain_core.runnables import RunnableLambda
from langchain_core.caches import InMemoryCache
from .Tools import search,get_info_from_local,set_current_session_id,set_current_user_id,create_todo,create_transaction

from dotenv import load_dotenv as _load_dotenv
_load_dotenv()
import os
import asyncio  # 新增
from functools import lru_cache  # 新增

# 添加缓存
from langchain_core.globals import set_llm_cache
set_llm_cache(InMemoryCache())

# 导入其他模块
try:
    from .Prompt import PromptClass
    from .Memory import MemoryClass
    from .Emotion import EmotionClass

except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from Prompt import PromptClass
    from Memory import MemoryClass
    from Emotion import EmotionClass

# 通过 LRU 缓存复用大模型客户端（单例）
@lru_cache(maxsize=1)
def _get_chatmodel():
    modelname = os.getenv("DEEPSEEK_MODEL_NAME")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE")
    return ChatDeepSeek(model=modelname, api_key=api_key, api_base=api_base)



class AgentClass:
    def __init__(self,user_id,session_id,streaming:bool=False):

        self.modelname = os.getenv("DEEPSEEK_MODEL_NAME")
        self.chatmodel =ChatDeepSeek(model=self.modelname,api_key=os.getenv("DEEPSEEK_API_KEY"),api_base=os.getenv("DEEPSEEK_API_BASE"),streaming=streaming)
        # 初始化空的工具列表
        self.tools = [search,get_info_from_local,create_todo,create_transaction]
        self.memorykey = os.getenv("MEMORY_KEY")
        self.memory = MemoryClass(memorykey=self.memorykey,model=self.modelname)
        self.emotion = EmotionClass(model=self.modelname)
        self.user_id = user_id
        self.session_id = session_id
        # 初始化情绪状态
        self.feeling = {"feeling":"default","score":5}
        
        # 创建动态 agent 执行器
        self.agent_executor = self._create_dynamic_agent()

    def _create_dynamic_agent(self):
        """使用 RunnableLambda 创建动态 agent 执行器"""
        
        def build_agent_chain(inputs):
            """动态构建 agent chain 的函数"""
            # 使用当前最新的情绪状态创建 prompt
            current_prompt = PromptClass(
                memorykey=self.memorykey, 
                feeling=self.feeling
            ).Prompt_Structure()
            
            set_current_session_id(self.session_id)
            set_current_user_id(self.user_id)

            # 创建 agent
            agent = create_tool_calling_agent(
                self.chatmodel,
                tools=self.tools,
                prompt=current_prompt,
            )
            
            # 创建 executor
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory.set_memory(session_id=self.session_id),
                verbose=True
            )
            
            # 执行并返回结果
            return executor.invoke(inputs)
        
        # 返回 RunnableLambda，它会在每次调用时动态构建链
        return RunnableLambda(build_agent_chain)

    def run_agent(self, input, callbacks=None):
        """运行 agent（支持回调）"""
        try:
            detected_feeling = self.emotion.Emotion_Sensing(input)
            if detected_feeling:
                self.feeling = detected_feeling
            response = self.agent_executor.invoke(
                {"input": input},
                config={"callbacks": callbacks or []}
            )
            return response
        except Exception as e:
            # 不向外抛，返回结构化输出，视图层将以 200 返回
            return {"output": f"抱歉，处理时出现错误：{str(e)}"}
