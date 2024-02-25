from django.urls import path
from . import views
from .views import AccountView

urlpatterns = [
    path('account/', AccountView.as_view(), name='account'),
    path('accounts/all/', AccountView.as_view(), name='account-details'),
    path('accounts/<int:account_id>/details/', AccountView.as_view(), name='account-details'),
]