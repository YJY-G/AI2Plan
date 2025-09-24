from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Account(models.Model):
    """
    账户模型，例如：现金、银行卡、支付宝、微信等
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    """
    分类模型，例如：餐饮、交通、购物、工资、奖金等
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=(('income', 'Income'), ('expense', 'Expense')))  # 收入或支出
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    """
    交易记录模型
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=10,
        choices=(('income', 'Income'), ('expense', 'Expense')),
        default='expense'
    )

    def __str__(self):
        return f"{self.date} - {self.amount} - {self.category.name}"

