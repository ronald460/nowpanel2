from django.urls import path
from  .views import *
from drivers import views

urlpatterns = [

    path('conductores/', views.driver, name='driver'),
    path('api/conductores/all_drivers/', views.lista_driver, name='lista_driver'),
    path('conductores/<str:id>/', views.driver_details, name='detalle_conductor'),
    path('active_driver/<str:id>/', active_driver, name='active_driver'),
    path('upload-photo/<str:id>/', upload_photo, name='upload_photo'),
    path('conductores_mov/<str:id>/', movement_driver, name='movement_driver'),
    path('conductores_car/', views.driv_car, name='driver-car'),
    path('api/conductor_carros/all_drivers_car/', views.list_driv_aprv_car_pend, name='list_driver_car'),

    #--------------------------------------------------------------------

    # path('maps/', views.mapa, name='mapa'),
    # path('api/conductores/', views.api_conductores, name='api_conductores'),
    # path('api/ruta/', views.api_ruta, name='api_ruta')

] 