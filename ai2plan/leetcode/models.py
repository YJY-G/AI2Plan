from django.db import models
from users.models import User

# Create your models here.
class Leetcode(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    description = models.TextField(default='')
    solution = models.TextField(default='')  # 解题方法/代码
    thinking = models.TextField(default='')  # 解题思路
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title