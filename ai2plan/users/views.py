# views.py
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import UserLoginSerializer, UserRegisterSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import ValidationError

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):  
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError) as e:
            # 记录日志，方便调试
            print(f"RefreshTokenView 错误: {e}")
            return Response(
                {"error": "无效的刷新令牌"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 获取访问令牌的过期时间
        access_token = serializer.validated_data["access"]
        # Token 中包含过期时间，无需手动计算
        # expires_in = token.payload['exp'] - int(timezone.now().timestamp())

        data = {
            "access": access_token,
            # 直接从 token 中获取过期时间
            # "expires_in": expires_in, #  不再需要 expires_in, 前端可以自己解码 access token 获取
        }
        return Response(data)

