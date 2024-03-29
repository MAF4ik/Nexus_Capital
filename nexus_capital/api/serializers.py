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


class MobilePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePayment
        fields = '__all__'

class UtilityPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityPayment
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'               

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'

class  ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'        
