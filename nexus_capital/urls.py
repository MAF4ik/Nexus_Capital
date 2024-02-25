from django.urls import path, include

from nexus_capital import views

urlpatterns = [
    path('ping', views.ping, name='ping'),
    path('api/', include('nexus_capital.api.urls'))
]
