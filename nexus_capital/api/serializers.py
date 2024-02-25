from rest_framework import serializers
from nexus_capital.models import *


class BankUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankUser
        fields = ['id', 'username', 'password', "first_name", "last_name", 'is_superuser', 'is_deleted']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = BankUser.objects.create_user(**validated_data)
        return user


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'                

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = '__all__'                
