from cProfile import label

from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    age = models.IntegerField(null=True, blank=True)
    emergencyContact1 = models.CharField(max_length=15, null=True, blank=True)
    emergencyContact2 = models.CharField(max_length=15, null=True, blank=True)

class Heartbeat(models.Model):
    value = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Oxygen(models.Model):
    value = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

class FallDetection(models.Model):
    value = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)