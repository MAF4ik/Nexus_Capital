from django.urls import path
from . import views
from .views import AccountView, CardView, UserView

urlpatterns = [
    path('account/', AccountView.as_view(), name='account'),
    path('account/<int:account_id>/', AccountView.as_view(), name='account-details'),
    path('account/<int:account_id>/details/', AccountView.as_view(), name='account-details'),
    path('user/', UserView.as_view(), name='user'),
    path('user/<int:user_id>/', UserView.as_view(), name='users'),
    path('user/<int:user_id>/details/', UserView.as_view(), name='user-details'),
    path('card/', CardView.as_view(), name='card')
]