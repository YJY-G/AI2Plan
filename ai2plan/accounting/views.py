from rest_framework import viewsets
from rest_framework import permissions
from .models import Account, Category, Transaction
from .serializers import AccountSerializer, CategorySerializer, TransactionSerializer
from django.db import transaction as db_transaction
from django.db.models import F

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]  # 必须登录才能访问

    def get_queryset(self):
        """
        只返回当前用户的账户
        """
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        创建账户时，自动关联当前用户
        """
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]  # 必须登录才能访问

    def get_queryset(self):
        """
        只返回当前用户的分类
        """
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        创建分类时，自动关联当前用户
        """
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]  # 必须登录才能访问

    def get_queryset(self):
        """
        只返回当前用户的交易记录
        """
        return Transaction.objects.filter(user=self.request.user)

    @db_transaction.atomic
    def perform_create(self, serializer):
        """
        创建交易：收入增加账户余额；支出减少账户余额
        """
        obj = serializer.save(user=self.request.user)
        if obj.transaction_type == 'income':
            obj.account.balance = F('balance') + obj.amount
        else:
            obj.account.balance = F('balance') - obj.amount
        obj.account.save(update_fields=['balance'])

    @db_transaction.atomic
    def perform_update(self, serializer):
        """
        更新交易：先撤销旧记录对旧账户的影响，再施加新记录对新账户的影响
        """
        old = self.get_object()
        old_account = old.account
        old_amount = old.amount
        old_type = old.transaction_type

        obj = serializer.save()

        # 撤销旧值
        if old_type == 'income':
            old_account.balance = F('balance') - old_amount
        else:
            old_account.balance = F('balance') + old_amount
        old_account.save(update_fields=['balance'])

        # 施加新值
        if obj.transaction_type == 'income':
            obj.account.balance = F('balance') + obj.amount
        else:
            obj.account.balance = F('balance') - obj.amount
        obj.account.save(update_fields=['balance'])

    @db_transaction.atomic
    def perform_destroy(self, instance):
        """
        删除交易：撤销其对账户余额的影响
        """
        if instance.transaction_type == 'income':
            instance.account.balance = F('balance') - instance.amount
        else:
            instance.account.balance = F('balance') + instance.amount
        instance.account.save(update_fields=['balance'])
        super().perform_destroy(instance)