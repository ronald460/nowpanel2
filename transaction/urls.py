from django.urls import path
from  .views import *
from transaction import views

urlpatterns = [

    path('transacciones/', views.transaction, name='transacciones'),
    path('api/transacciones/all_transaction/', views.list_transaction, name='list_transaction'),

] 