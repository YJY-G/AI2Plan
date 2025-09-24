from rest_framework import serializers
from .models import Account, Category, Transaction

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('user',)  # 设置 user 字段为只读

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('user',)  # 设置 user 字段为只读

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user',)  # 设置 user 字段为只读

    def create(self, validated_data):
        """
        创建交易记录时，自动关联当前用户
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)