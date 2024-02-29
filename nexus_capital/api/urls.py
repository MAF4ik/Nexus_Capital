from django.urls import path
from . import views
from .views import AccountView, CardView, UserView, ServiceView, TransactionView

urlpatterns = [
    path('user/', UserView.as_view(), name='user'),
    path('user/<int:user_id>/', UserView.as_view(), name='users'),
    path('user/<int:user_id>/details/', UserView.as_view(), name='user-details'),
    path('account/', AccountView.as_view(), name='account'),
    path('account/<int:account_id>/', AccountView.as_view(), name='account-delete'),
    path('account/<int:account_id>/details/', AccountView.as_view(), name='account-details'),
    path('card/', CardView.as_view(), name='card'),
    path('card/<int:card_id>/', CardView.as_view(), name='card-delete'),
    path('card/<int:card_id>/details/', CardView.as_view(), name='card-details'),
    path('service/', ServiceView.as_view(), name='service'),
    path('service/<int:service_id>/', ServiceView.as_view(), name='service-delete'),
    path('service/<int:service_id>/details/', ServiceView.as_view(), name='service-details'),
    path('transaction/', TransactionView.as_view(), name='transaction')

]