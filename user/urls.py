from django.urls import path
from  .views import *
from user import views

urlpatterns = [

    path('usuarios/', views.usuarios, name='usuarios'),
    path('api/usuarios/all_users/', views.lista_users, name='lista_users'),
    path('believe_user/<str:id>/', views.believe_user, name='believe_user'),
   
] 