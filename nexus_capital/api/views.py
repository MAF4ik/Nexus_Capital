from django.shortcuts import get_object_or_404
from rest_framework import status
from nexus_capital.models import Account, BankUser, Card
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Max
from .serializers import *
import random


def get_max_account_number():
    max_acc_num = Account.objects.aggregate(max_account_number=Max('account_number'))
    return max_acc_num['max_account_number']

def get_max_card_number():
    max_card_num = Card.objects.aggregate(max_card_number=Max('card_number'))
    return max_card_num['max_card_number']

def random_account_number():
    max_account_number = get_max_account_number()

    if max_account_number is None:
        max_account_number = '2105000000001'
        return max_account_number
    else:
        max_account_number = str(int(max_account_number) + random.randint(1, 21))
        return max_account_number
    
def random_card_number():
    max_card_number = get_max_card_number()

    if max_card_number is None:
        max_card_number = '5605000000001'
        return max_card_number
    else:
        max_card_number = str(int(max_card_number) + random.randint(1, 21))
        return max_card_number    


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

class UserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
   
    def get(self, request, user_id=None):
        token_id = get_user_id_from_token(request)
        user_admin = BankUser.objects.get(id=token_id)
        admin = user_admin.is_superuser
        if admin == True:
            if user_id is None:
                print(user_id)
                user = BankUser.objects.all()
                serializer = BankUserSerializer(user, many=True)
                return Response(serializer.data)
            
            if user_id is not None:
                print(user_id)
                user = get_object_or_404(BankUser, id=user_id, is_deleted=False,)
                serializer = BankUserSerializer(user)
                return Response(serializer.data)
            else:
                return Response({"message":"You do not have access to this route"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user_id = get_user_id_from_token(request)
        user = get_object_or_404(BankUser, id=user_id, is_deleted=False)
        accounts = Account.objects.filter(user=user_id, is_deleted=False)
        cards = Card.objects.filter(user=user_id, is_deleted=False)

        # Проверяем все счета пользователя
        for account in accounts:
            if account.balance != 0:
                return Response({"message": "You cannot delete an account with a balance"},
                                status=status.HTTP_400_BAD_REQUEST)
            if cards.filter(account=account).exists():
                return Response({"message": "You cannot delete an account with a card"},
                                status=status.HTTP_400_BAD_REQUEST)

            

        accounts.update(is_deleted=True)
        cards.update(is_deleted=True)

        user.is_deleted = True
        user.save()

        return Response({"message": "Accounts deleted successfully"}, status=status.HTTP_200_OK)


class AccountView(APIView):
        
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get(self, request, account_id=None):
           
        user_id = get_user_id_from_token(request)
        user = get_object_or_404(BankUser, id=user_id, is_deleted=False)
        admin = user.is_superuser
        if admin == True:
            accounts = Account.objects.all()
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data)
       
        if account_id is not None:
            account = get_object_or_404(Account, id=account_id, user=user_id, is_deleted=False)
            serializer = AccountSerializer(account)
            return Response(serializer.data)
    
        if account_id is None:
            accounts = Account.objects.filter(user=user_id, is_deleted=False)
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data)
       
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
    def post(self, request):
        user_id = get_user_id_from_token(request)
        user = get_object_or_404(BankUser, id=user_id, is_deleted=False)
        role = user.is_superuser
        if role == False:
            account_number = random_account_number()
            created_account = Account.objects.create(account_number=account_number, user=user)
            serializer = AccountSerializer(created_account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif role == True:
            return Response({"message":"This user is an admin and cannot have an account."}, status=status.HTTP_403_FORBIDDEN)
        
    def delete(self, request, account_id=None):
        user_id = get_user_id_from_token(request)
        account = get_object_or_404(Account, id=account_id, user=user_id, is_deleted=False)
        
        if account.balance != 0:
            return Response({"message": "You cannot delete an account with a balance"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif account.type == "checking":
            account.is_deleted = True
            account.save()
            Card.objects.filter(account=account).update(is_deleted=True)

        else:    
            account.is_deleted = True
            account.save()
        return Response({"message": "The account was successfully deleted"}, status=status.HTTP_200_OK)
        
class CardView(APIView): 
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, card_id=None):
        user_id = get_user_id_from_token(request)
        user = BankUser.objects.get(id=user_id)
        admin = user.is_superuser
        if admin:
            cards = Card.objects.all()
            serializer = CardSerializer(cards, many=True)
            serialized_data = serializer.data

            for data in serialized_data:
                card_id = data['id']
                account = Account.objects.get(card__id=card_id)
                data['account_balance'] = account.balance

            return Response(serialized_data)

        if card_id is not None:
            card = get_object_or_404(Card, id=card_id, user=user_id, is_deleted=False)
            serializer = CardSerializer(card)
            serialized_data = serializer.data
            serialized_data['account_balance'] = card.account.balance
            return Response(serialized_data)

        if card_id is None:
            cards = Card.objects.filter(user=user_id, is_deleted=False)
            serializer = CardSerializer(cards, many=True)
            serialized_data = serializer.data

            for data in serialized_data:
                card_id = data['id']
                account = Account.objects.get(card__id=card_id)
                data['account_balance'] = account.balance

            return Response(serialized_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        user_id = get_user_id_from_token(request)
        user = BankUser.objects.get(id=user_id)
        role = user.is_superuser
        if not role:
            account_number = random_account_number()
            created_account = Account.objects.create(account_number=account_number, user=user, type="checking")
            created_card = Card.objects.create(card_number=random_account_number(), account=created_account, user=user)
            serializer = CardSerializer(created_card)
            serialized_data = serializer.data
            serialized_data['account_balance'] = created_account.balance
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        elif role:
            return Response({"message": "This user is an admin and cannot have an account."}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, card_id=None):
        user_id = get_user_id_from_token(request)
        if card_id is not None:

            card = get_object_or_404(Card, id=card_id, user=user_id, is_deleted=False)
            account = card.account
            if card.account.balance != 0:
                return Response({"message": "You cannot delete a card associated with an account with a balance"},
                                status=status.HTTP_400_BAD_REQUEST)
            Account.objects.filter(id=account.id).update(is_deleted=True)
            card.is_deleted = True
            card.save()
                  

            return Response({"message": "Card deleted successfully"}, status=status.HTTP_200_OK)

        return Response({"message": "Card ID is required"}, status=status.HTTP_400_BAD_REQUEST)
