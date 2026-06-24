from django.urls import path
from  .views import *
from dashboard import views

urlpatterns = [

    path('home/', views.dashboard, name='home'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_stats'),
    path('api/usuarios/result/', views.api_usuarios, name='api_usuarios'),
    path('api/viajes-por-dia/', views.api_viajes_por_dia, name='api_viajes'),
] 