from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType



class BankUser(User):
    is_deleted = models.BooleanField(default=False)

class Account(models.Model):
    account_number = models.CharField(max_length=32, unique=True)   
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)


class Card(models.Model):
    card_number = models.CharField(max_length=52, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)

class Transaction(models.Model):
    amount = models.IntegerField(null=False) 
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)
    content_type_from = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='transactions_from')
    object_id_from = models.PositiveIntegerField()
    content_object_from = GenericForeignKey('content_type_from', 'object_id_from')
    content_type_to = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='transactions_to')
    object_id_to = models.PositiveIntegerField()
    content_object_to = GenericForeignKey('content_type_to', 'object_id_to')


class ServiceCategory(models.Model):
    type = models.CharField(max_length=32)
    is_deleted = models.BooleanField(default=False)

class Service(models.Model):
    title = models.CharField(null=False, max_length=32, unique=True)
    description = models.TextField(default='No description')
    is_deleted = models.BooleanField(default=False)
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)

class MobilePayment(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE) 
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)
    number = models.CharField(max_length=255)


class UtilityPayment(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE) 
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE)
    customer_account_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

