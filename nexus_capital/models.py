from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User



class BankUser(User):
    
    is_deleted = models.BooleanField(default=False)

class Account(models.Model):

    account_number = models.CharField(max_length=32, unique=True)   
    balance = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)

class Service(models.Model):
    
    title = models.CharField(null=False, max_length=32)
    balance = models.IntegerField(default=0)
    description = models.TextField(default='No description')

class Payment(models.Model):

    amount = models.IntegerField(null=False)
    account_number =models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    title_service = models.CharField(null=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    
class Transfer(models.Model):

    amount = models.IntegerField(null=False) 
    created_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(default='No description')
    account_from = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='outgoing_transactions')
    account_to = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='incoming_transactions')

class Card(models.Model):
    
    card_number = models.CharField(max_length=32, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)

class ServiceCatigories(models.Model):
    type = models.CharField(max_length=32)
    id_service = models.ForeignKey('Service', on_delete=models.CASCADE)
    