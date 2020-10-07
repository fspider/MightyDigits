from django.db import models
from django.utils import timezone
from django.contrib.auth import (
    get_user_model
)
User = get_user_model()

# Create your models here.
class AdminSetting(models.Model):
    user = models.ForeignKey(User, db_column="user", on_delete=models.CASCADE, null=True)
    key = models.TextField(max_length=1000)
    value = models.TextField(max_length=1000)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def getField(key):
        try:
            item = AdminSetting.objects.get(key=key)
            result = item.value
        except AdminSetting.DoesNotExist:
            result = ""
        return result