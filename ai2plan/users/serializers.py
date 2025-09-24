from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_username(self, value):
        User = get_user_model()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def create(self, validated_data):
        User = get_user_model()
        user = User(username=validated_data["username"])
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserLoginSerializer(TokenObtainPairSerializer):  
    # 继承自JWT基础序列化器  
    def validate(self, attrs):  
        # 调用父类验证逻辑生成Token  
        data = super().validate(attrs)  

        # 添加自定义响应字段  
        data.update({  
            "user_id": self.user.userid,  
            "username": self.user.username,
        })
        return data