from django.db import models

# Create your models here.

class Chat(models.Model):
    file = models.FileField(upload_to='chats/')
    
