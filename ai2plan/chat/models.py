from django.db import models
from users.models import User

# Create your models here.
class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='histories')
    session_id = models.CharField(unique=True,max_length=255)

    def __str__(self):
        return self.session_id
