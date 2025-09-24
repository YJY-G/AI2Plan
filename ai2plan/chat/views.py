from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .src.Agents import AgentClass
from .src.Storage import add_user, get_user
from .src.Memory import MemoryClass
from .models import History
from .serializers import ChatSerializer,HistorySerializer
from rest_framework import permissions
from rest_framework import status
from .src.addDoc import DocumentProcessor
import os
from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from langchain_core.callbacks import BaseCallbackHandler
import queue
import threading
import json
import time

# Create your views here.
class HistoryViewSet(ModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return History.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        base_data = self.serializer_class(instance).data
        memory = MemoryClass(memorykey=instance.session_id)
        chat_history = memory.get_memory(session_id=instance.session_id)
        resp = dict(base_data)
        resp['memory'] = chat_history.messages
        return Response(resp)

class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSerializer

    def post(self, request, *args, **kwargs):
        user_id = request.user.userid
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            session_id = serializer.validated_data['session_id']
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        agent = AgentClass(user_id,session_id)
        try:
            response = agent.run_agent(message)
            
            # 提取回复内容
            if isinstance(response, dict):
                ai_response = response.get('output', str(response))
            else:
                ai_response = str(response)
            
            return Response({
                'response': ai_response,
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'错误: {str(e)}',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class AddDocView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        urls = request.data.get('urls', [])
        document_processor = DocumentProcessor(persist_directory=os.getenv("PERSIST_DIR"))
        result = document_processor.add_urls(urls)
        return Response(result, status=status.HTTP_200_OK)

class StreamCallback(BaseCallbackHandler):
    def __init__(self, q: queue.Queue):
        self.q = q

    # ============ Token 流 ============
    def on_llm_new_token(self, token, **kwargs):
        if token:
            self.q.put(token)

    def on_llm_end(self, *args, **kwargs):
        self.q.put(None)

    def on_llm_error(self, error, **kwargs):
        self._event("error", {"message": str(error)})
        self.q.put(f"[ERROR]{str(error)}")
        self.q.put(None)

    def on_chain_error(self, error, **kwargs):
        self._event("error", {"message": str(error)})
        self.q.put(f"[ERROR]{str(error)}")
        self.q.put(None)

    # ============ 进度事件 ============
    def on_chain_start(self, serialized, inputs, **kwargs):
        name = (serialized or {}).get("name") or (serialized or {}).get("id") or "chain"
        self._event("chain_start", {"name": name, "inputs": self._safe(inputs)})

    def on_chain_end(self, outputs, **kwargs):
        self._event("chain_end", {"outputs": self._safe(outputs)})

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = (serialized or {}).get("name") or "tool"
        self._event("tool_start", {"name": name, "input": self._safe(input_str)})

    def on_tool_end(self, output, **kwargs):
        # 避免把大段文档原文直接塞进事件，可仅传长度
        out_preview = output if isinstance(output, str) and len(output) < 500 else f"[len={len(str(output))}]"
        self._event("tool_end", {"output": out_preview})

    # ============ 帮助方法 ============
    def _event(self, etype: str, payload: dict):
        try:
            data = json.dumps({"type": etype, "payload": payload}, ensure_ascii=False)
        except Exception:
            data = json.dumps({"type": etype, "payload": str(payload)}, ensure_ascii=False)
        # 单独一条队列消息并带换行，降低与 token 拼接的概率
        self.q.put("\n[EVENT]" + data + "\n")

    def _safe(self, obj):
        try:
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            return json.loads(json.dumps(obj, ensure_ascii=False, default=str))
        except Exception:
            return str(obj)

class ChatStreamView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSerializer

    def post(self, request, *args, **kwargs):
        user_id = request.user.userid
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']
        session_id = serializer.validated_data['session_id']

        q = queue.Queue(maxsize=1000)
        cb = StreamCallback(q)

        def run():
            try:
                agent = AgentClass(user_id, session_id, streaming=True)
                agent.run_agent(message, callbacks=[cb])
            except Exception as e:
                q.put(f"[ERROR]{str(e)}")
            finally:
                q.put(None)

        t = threading.Thread(target=run, daemon=True)
        t.start()

        def event_stream():
            yield ""  # 触发 header 发送
            last_flush = time.time()
            buf = []
            while True:
                try:
                    item = q.get(timeout=0.1)
                except queue.Empty:
                    # 定时心跳，避免中间层缓冲
                    if time.time() - last_flush > 10:
                        yield "\n"
                        last_flush = time.time()
                    continue
                if item is None:
                    if buf:
                        chunk = "".join(buf)
                        yield chunk
                        buf = []
                    break
                buf.append(item)
                # 小批量聚合，减少过多系统调用
                if len(buf) >= 10 or (time.time() - last_flush) > 0.2:
                    chunk = "".join(buf)
                    yield chunk
                    buf = []
                    last_flush = time.time()
            yield "[DONE]"

        resp = StreamingHttpResponse(event_stream(), content_type='text/plain; charset=utf-8')
        resp['Cache-Control'] = 'no-cache'
        resp['X-Accel-Buffering'] = 'no'  # 兼容 Nginx 关闭缓冲
        return resp
        