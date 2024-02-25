from django.shortcuts import get_object_or_404
from rest_framework import status
from nexus_capital.models import Account, BankUser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Max
from .serializers import BankUserSerializer, AccountSerializer
from django.contrib.auth.models import User
import random


def get_max_account_number():
    max_acc_num = Account.objects.aggregate(max_account_number=Max('account_number'))
    return max_acc_num['max_account_number']


def random_account_number():
    max_account_number = get_max_account_number()

    if max_account_number is None:
        max_account_number = '2105000000000001'
        return max_account_number
    else:
        max_account_number = str(int(max_account_number) + random.randint(1, 21))
        return max_account_number


def get_user_id_from_token(request):
    try:
        authorization_header = request.headers.get('Authorization')
        access_token = AccessToken(authorization_header.split()[1])
        user_id = access_token['user_id']
        return user_id
    except (AuthenticationFailed, IndexError):
        return None
    

@api_view(["POST"])
def create_user(request):
    serializer = BankUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   

class AccountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id=None):
       user_id = get_user_id_from_token(request)
       user = BankUser.objects.get(id=user_id)
       is_deleted = user.is_deleted

       if account_id is not None:
           account = self.get_object(account_id)
           serializer = AccountSerializer(account)
           return Response(serializer.data)
      
       else:
           accounts = Account.objects.filter(user=user_id, is_deleted=False)
           serializer = AccountSerializer(accounts, many=True)
           return Response(serializer.data)
       
    def post(self, request):
        user_id = get_user_id_from_token(request)
        user = BankUser.objects.get(id=user_id)
        role = user.is_superuser
        print(role)
        if role == False:
            Account(account_number=random_account_number(), user=user).save()
            return Response(status=status.HTTP_201_CREATED) 
        else:
            return Response({"message:":"You do not have access to this route"}, status=status.HTTP_403_FORBIDDEN)
        

    def get_object(self, account_id):
        try:
            return Account.objects.get(pk=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
         
   
       
