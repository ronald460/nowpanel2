from django.urls import path
from  .views import *
from travel import views

urlpatterns = [

    path('viajes/', views.viajes, name='travels'),
    path('api/viajes/all_travels/', lista_travels, name='lista_travel'),
    path('details_travel/<str:id>/', views.details_travel, name='details_travel'),
    path('api/report-travels/', report_travels, name='report_travels'),
    path('api/export-excel-report/', export_excel_report, name='export_excel_report'),

] 