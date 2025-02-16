from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    email=models.EmailField(unique=True)
    username=models.CharField(unique=False,max_length=50)
    subscription=models.BooleanField(default=False)
    USERNAME_FIELD="email"

    REQUIRED_FIELDS=["username"]
    

    def __str__(self):
        return self.username