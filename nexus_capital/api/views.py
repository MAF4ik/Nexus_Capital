from django.db.models import Sum
from django.db import transaction
from rest_framework import status
from nexus_capital.models import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Max
from .serializers import *
import random
import datetime


def created_at():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

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
        if 'is_superuser' in request.data  or 'is_deleted' in request.data:
            return Response({"message":"Changing is_superuser, is_deleted is not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def set_superuser(request, user_id):
    current_user = request.user
    if current_user.is_superuser:
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
            user.is_superuser = True
            user.save()
            return Response({'message': 'User is now a superuser.'})
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=404) 
    else:
        return Response({"message": "You do not have access to this route"}, status=400)
    
class UserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id=None):
        token_id = get_user_id_from_token(request)
        try:
            user_admin = BankUser.objects.get(id=token_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message": "Admin not found."}, status=status.HTTP_404_NOT_FOUND) 
        if user_admin.is_superuser:

            if user_id is None:
                user = BankUser.objects.filter(is_deleted=False,)
                serializer = BankUserSerializer(user, many=True)
                return Response(serializer.data)
            
            if user_id is not None:
                try:
                    user = BankUser.objects.get(id=user_id, is_deleted=False)
                    serializer = BankUserSerializer(user)
                    return Response(serializer.data)
                except BankUser.DoesNotExist:
                    return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
                
            else:
                return Response({"message":"You do not have access to this route"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
            serializer = BankUserSerializer(user, data=request.data, partial=True)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
        if 'password' in request.data or 'is_deleted' in request.data or 'is_superuser' in request.data:
            return Response({"message":"Changing password, is_deleted, is_superuser is not allowed."}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "BankUser updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        accounts = Account.objects.filter(user=user_id, is_deleted=False)
        cards = Card.objects.filter(user=user_id, is_deleted=False)

        balance_sum = accounts.aggregate(Sum('balance'))['balance__sum']
        if balance_sum != 0:
            return Response({"message": "You cannot delete an account with a balance"}, status=status.HTTP_400_BAD_REQUEST)

        if cards.filter(account__in=accounts).exists():
            return Response({"message": "You cannot delete an account with a card"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            accounts.update(is_deleted=True)
            cards.update(is_deleted=True)

            user.is_deleted = True
            user.save()

        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


class AccountView(APIView):
        
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id=None):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
        if user.is_superuser:
            accounts = Account.objects.all()
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data)
       
        if account_id is not None:
            try:
                account = Account.objects.get(id=account_id, user=user_id, is_deleted=False)
                serializer = AccountSerializer(account)
                return Response(serializer.data)
            except Account.DoesNotExist:
                return Response({"message": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if account_id is None:
            accounts = Account.objects.filter(user=user_id, is_deleted=False)
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data)
       
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
    def post(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user.is_superuser :

            created_account = Account.objects.create(
                account_number=random_account_number(), 
                created_at=created_at(),
                user=user 
                )
            serializer = AccountSerializer(created_account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"message":"This user is an admin and cannot have an account."}, status=status.HTTP_403_FORBIDDEN)
        
    def delete(self, request, account_id=None):
        user_id = get_user_id_from_token(request)
        try:
            account = Account.objects.get(id=account_id, user=user_id, is_deleted=False)
        except Account.DoesNotExist:
            return Response({"message": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            card = Card.objects.get(account=account, is_deleted=False)
        except Card.DoesNotExist:
            card = None
        if account.balance != 0:
            return Response({"message": "You cannot delete an account with a balance"}, status=status.HTTP_400_BAD_REQUEST)
        if card is not None:
            return Response({"message": "You cannot delete an account with a card"}, status=status.HTTP_400_BAD_REQUEST)
        else:    
            account.is_deleted = True
            account.save()
        return Response({"message": "The account was successfully deleted"}, status=status.HTTP_200_OK)
        
class CardView(APIView): 
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, card_id=None):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_superuser:
            cards = Card.objects.all()
            serializer = CardSerializer(cards, many=True)
            serialized_data = serializer.data

            for data in serialized_data:
                card_id = data['id']
                account = Account.objects.get(card__id=card_id)
                data['account_balance'] = account.balance

            return Response(serialized_data)

        if card_id is not None:
            try:
                card = Card.objects.get(id=card_id, user=user_id, is_deleted=False)
                serializer = CardSerializer(card)
                serialized_data = serializer.data
                serialized_data['account_balance'] = card.account.balance
                return Response(serialized_data)
            except Card.DoesNotExist:
                return Response({"message":"Card not found"})    

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
        try:
            user = BankUser.objects.get(id=user_id)
        except BankUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_superuser:
            created_account = Account.objects.create(
                account_number=random_account_number(), 
                created_at=created_at(), 
                user=user
                )
            created_card = Card.objects.create(
                card_number=random_card_number(), 
                account=created_account, 
                created_at=created_at(),
                user=user
                )
            serializer = CardSerializer(created_card)
            serialized_data = serializer.data
            serialized_data['account_balance'] = created_account.balance
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        elif user.is_superuser:
            return Response({"message": "This user is an admin and cannot have an account."}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, card_id=None):
        user_id = get_user_id_from_token(request)
        if card_id is not None:
            card = Card.objects.get(id=card_id, user=user_id, is_deleted=False)
            if card.account.balance != 0:
                return Response({"message": "You cannot delete a card associated with an account with a balance"},
                                status=status.HTTP_400_BAD_REQUEST)
            Account.objects.filter(id=card.account.id).update(is_deleted=True)
            card.is_deleted = True
            card.save()
            return Response({"message": "Card deleted successfully"}, status=status.HTTP_200_OK)

        return Response({"message": "Card ID is required"}, status=status.HTTP_400_BAD_REQUEST)


class ServiceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, service_id=None):
        if service_id:
            try:
                service = Service.objects.get(id=service_id, is_deleted=False)
                serializer = ServiceSerializer(service)
                return Response(serializer.data)
            except Service.DoesNotExist:
                return Response({"message": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

        services = Service.objects.filter(is_deleted=False)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
    
    def post(self, request, service_category_id):
        user = request.user
        if user.is_superuser:
            try:
                service_category = ServiceCategory.objects.get(id=service_category_id, is_deleted=False)
            except ServiceCategory.DoesNotExist:
                return Response({"message": "Service Category not found."}, status=status.HTTP_404_NOT_FOUND)
            
            request.data['service_category'] = service_category.id
            
            serializer = ServiceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_403_FORBIDDEN)
        
    def patch(self, request, service_id):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id)
        except BankUser.DoesNotExist:
            return Response({"message":"User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_superuser:
            try:
                service = Service.objects.get(id=service_id, is_deleted=False)
            except Service.DoesNotExist:
                return Response({"message":"Service not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ServiceSerializer(service, data=request.data, partial=True)
            if serializer.is_valid():
                if 'is_deleted' in request.data or "service_category" in request.data:
                    return Response({"message":"Changing is_deleted, service_category is not allowed."}, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response({"Service updated successfully": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, service_id):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message":"User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_superuser:
            try:
                service = Service.objects.get(id=service_id, is_deleted=False)
            except Service.DoesNotExist:
                return Response({"message":"Service not found."}, status=status.HTTP_404_NOT_FOUND)
            service.is_deleted = True
            service.save()
            return Response({"message": "Service deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_400_BAD_REQUEST)
        
class ServiceCategoriesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, service_category_id=None):

        if service_category_id is None:
            service_categories = ServiceCategory.objects.filter(is_deleted=False)
            serializer = ServiceCategorySerializer(service_categories, many=True)
            return Response(serializer.data)
        else:
            try:
                service_category = ServiceCategory.objects.get(id=service_category_id, is_deleted=False)
            except ServiceCategory.DoesNotExist:
                return Response({"message": "Service Category not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ServiceCategorySerializer(service_category)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        if user.is_superuser:
            serializer = ServiceCategorySerializer(data=request.data)
            if serializer.is_valid():
                if 'is_deleted' in request.data:
                    return Response({"message":"Changing is_deleted is not allowed."}, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_403_FORBIDDEN)
    
    def patch(self, request, service_category_id):
        user = request.user
        if user.is_superuser:
            try:
                service_categories = ServiceCategory.objects.get(id=service_category_id, is_deleted=False)
            except ServiceCategory.DoesNotExist:
                return Response({"message":"Service Category not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = ServiceCategorySerializer(service_categories, data=request.data, partial=True)
            if serializer.is_valid():
                if 'is_deleted' in request.data:
                    return Response({"message":"Changing is_deleted is not allowed."}, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response({"Service Category updated successfully": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_403_FORBIDDEN)
    
    def delete(self, request, service_category_id):
        user = request.user
        if user.is_superuser:
            try:
                service_category = ServiceCategory.objects.get(id=service_category_id, is_deleted=False)
            except ServiceCategory.DoesNotExist:
                return Response({"message": "Service Category not found."}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                service = Service.objects.filter(service_category=service_category.id, is_deleted=False).first()
            except Service.DoesNotExist:
                service = None
            
            if service is None:
                service_category.is_deleted = True
                service_category.save()
                return Response({"message": "Service Category deleted successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Service Category cannot be deleted as it has services."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You do not have access to this route"}, status=status.HTTP_403_FORBIDDEN)


class TransactionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message":"User not found."}, status=status.HTTP_404_NOT_FOUND)

        admin = user.is_superuser

        if admin:
            transactions = Transaction.objects.all()
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        else:
            transactions = Transaction.objects.filter(user_id=user_id)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)

    def patch(self, request):
        user_id = get_user_id_from_token(request)
        acc_num_from = request.data.get('account_from')
        acc_num_to = request.data.get('account_to')
        card_num_from = request.data.get('card_from')
        card_num_to = request.data.get('card_to')
        amount = request.data.get('amount')

        try:
            user = BankUser.objects.get(id=user_id, is_deleted=False)
        except BankUser.DoesNotExist:
            return Response({"message":"User not found."}, status=status.HTTP_404_NOT_FOUND)

        transaction_data = {
            'amount': amount,
            'created_at': created_at(),
            'user': user,
        }

        if acc_num_from and acc_num_to:
            acc_from = Account.objects.filter(account_number=acc_num_from, user=user, is_deleted=False).first()
            acc_to = Account.objects.filter(account_number=acc_num_to, is_deleted=False).first()

            if not acc_from:
                return Response({"message":"Account not found."}, status=status.HTTP_404_NOT_FOUND)

            if not acc_to:
                return Response({"message":"Destination account not found."}, status=status.HTTP_404_NOT_FOUND)

            if acc_from.balance < amount:
                return Response({"message":"Insufficient balance on the source account."}, status=status.HTTP_400_BAD_REQUEST)

            transaction_data['content_object_from'] = acc_from
            transaction_data['content_object_to'] = acc_to

        elif card_num_from and acc_num_to:
            card_from = Card.objects.filter(card_number=card_num_from, user_id=user_id, is_deleted=False).first()
            acc_to = Account.objects.filter(account_number=acc_num_to, is_deleted=False).first()

            if not card_from:
                return Response({"message":"Card not found."}, status=status.HTTP_404_NOT_FOUND)

            if not acc_to:
                return Response({"message":"Destination account not found."}, status=status.HTTP_404_NOT_FOUND)

            if card_from.account.balance < amount:
                return Response({"message":"Insufficient balance on the source card."}, status=status.HTTP_400_BAD_REQUEST)

            transaction_data['content_object_from'] = card_from.account
            transaction_data['content_object_to'] = acc_to

        elif acc_num_from and card_num_to:
            acc_from = Account.objects.filter(account_number=acc_num_from, user_id=user_id, is_deleted=False).first()
            card_to = Card.objects.filter(card_number=card_num_to, is_deleted=False).first()

            if not acc_from:
                return Response({"message":"Account not found."}, status=status.HTTP_404_NOT_FOUND)

            if not card_to:
                return Response({"message":"Destination card not found."}, status=status.HTTP_404_NOT_FOUND)

            if acc_from.balance < amount:
                return Response({"message":"Insufficient balance on the source account."}, status=status.HTTP_400_BAD_REQUEST)

            transaction_data['content_object_from'] = acc_from
            transaction_data['content_object_to'] = card_to.account

        elif card_num_from and card_num_to:
            card_from = Card.objects.filter(card_number=card_num_from, user_id=user_id, is_deleted=False).first()
            card_to = Card.objects.filter(card_number=card_num_to, user_id=user_id, is_deleted=False).first()

            if not card_from:
                return Response({"message":"Card not found."}, status=status.HTTP_404_NOT_FOUND)
            if not card_to:
                return Response({"message":"Destination card not found."}, status=status.HTTP_404_NOT_FOUND)

            if card_from.account.balance < amount:
                return Response({"message":"Insufficient balance on the source card."}, status=status.HTTP_400_BAD_REQUEST)

            transaction_data['content_object_from'] = card_from.account
            transaction_data['content_object_to'] = card_to.account
        else:
            return Response({"message":"You must specify either an account or a card."}, status=status.HTTP_400_BAD_REQUEST)

        transaction = Transaction.objects.create(**transaction_data)
        serializer = TransactionSerializer(transaction)

        transaction.content_object_from.balance -= transaction_data['amount']
        transaction.content_object_to.balance += transaction_data['amount']

        transaction.content_object_from.save()
        transaction.content_object_to.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, service_id):
        user_id = get_user_id_from_token(request)
        user = BankUser.objects.get(id=user_id)
        amount = request.data.get('amount')
        account_num = request.data.get('account_number')
        card_num = request.data.get('card_number')


        try:
            card = Card.objects.get(user=user, card_number=card_num, is_deleted=False)
        except Card.DoesNotExist:
            card = None
  
        try:
            account = Account.objects.get(user=user, account_number=account_num, is_deleted=False)
        except Account.DoesNotExist:
            account = None

        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"message":"Service not found."}, status=status.HTTP_404_NOT_FOUND)

        if service.service_category.type == "mobile":
            number = request.data.get('number')

            if card is not None:
                if card.account.balance < amount:
                    return Response({"message":"Insufficient balance on the source card."}, status=status.HTTP_400_BAD_REQUEST)

                payment = MobilePayment.objects.create(
                    amount=amount,
                    account=card.account,
                    created_at=created_at(),
                    service=service,  
                    user=user,
                    number=number
                )

                card.account.balance -= amount
                card.account.save()

                serializer = MobilePaymentSerializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            if account is not None:
                if account.balance < amount:
                    return Response({"message":"Insufficient balance on the source account."}, status=status.HTTP_400_BAD_REQUEST)

                payment = MobilePayment.objects.create(
                    amount=amount,
                    account=account,
                    created_at=created_at(),
                    service=service,  
                    user=user,
                    number=number
                )

                account.balance -= amount
                account.save()

                serializer = MobilePaymentSerializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        if service.service_category.type == "utility":

            customer_account_number = request.data.get('customer_account_number')
            address = request.data.get('address')

            if card is not None:
                if card.account.balance < amount:
                    return Response({"message":"Insufficient balance on the source card."}, status=status.HTTP_400_BAD_REQUEST)

                payment = UtilityPayment.objects.create(
                    amount=amount,
                    account=card.account,
                    created_at=created_at(),
                    service=service, 
                    user=user,
                    customer_account_number=customer_account_number,
                    address=address
                )

                card.account.balance -= amount
                card.account.save()

                serializer = UtilityPaymentSerializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            if account is not None:
                if account.balance < amount:
                    return Response({"message":"Insufficient balance on the source account."}, status=status.HTTP_400_BAD_REQUEST)
                
                payment = UtilityPayment.objects.create(
                    amount=amount,
                    account=account,
                    created_at=created_at(),
                    service=service, 
                    user=user,
                    customer_account_number=customer_account_number,
                    address=address
                )
                
                account.balance -= amount
                account.save()
                
                serializer = UtilityPaymentSerializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"message":'Account or card not found'})

        return Response({"message":"Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)