from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db import connections
from drivers.models import *
from user.models import *

def dashboard(request):

    context = {
        'is_admin': request.user.is_superuser
    }

    return render(request, 'dashboard.html', context)

def api_dashboard_stats(request):

    
    #redis_client = get_redis_connection('default')
    
    all_driver = Driver.objects.using('legacy').all().count()
    all_users = User.objects.using('legacy').all().count()
    

    # travels_data = get_redis_connection('travels')

    # if travels_data:
    #     travels_data = json.load(travels_data)

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM drivers d INNER JOIN vehicles v ON d.id = v.driver_id WHERE d.working = True AND v.type = 'CAR'")
        driver_car = cursor.fetchone()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM drivers d INNER JOIN vehicles v ON d.id = v.driver_id WHERE d.working = True AND v.type = 'VAN'")
        driver_van = cursor.fetchone()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM drivers d INNER JOIN vehicles v ON d.id = v.driver_id WHERE d.working = True AND v.type = 'MOTORCYCLE'")
        driver_moto = cursor.fetchone()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM drivers WHERE working = True")
        driver_working = cursor.fetchone()

    count_driver = driver_car + driver_van
    
    return JsonResponse({
        'all_driver': all_driver,
        'driver_car': count_driver,
        'driver_moto': driver_moto,
        'all_users': all_users,
        #'travel_data': travels_data,
        'driver_working': driver_working[0] if driver_working else 0
    })

def api_usuarios(request):
    """API que devuelve lista de usuarios"""
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT id, name, last_name, email, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        users = cursor.fetchall()
    
    usuarios_list = []
    for user in users:
        usuarios_list.append({
            'id': user[0],
            'name': f"{user[1]} {user[2]}",
            'email': user[3],
            'created_at': user[4].strftime('%Y-%m-%d %H:%M:%S') if user[4] else None
        })
    
    return JsonResponse(usuarios_list, safe=False)

def api_viajes_por_dia(request):
    
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=7)
    
    datos = []
    for i in range(7):
        fecha = fecha_inicio + timedelta(days=i)
        datos.append({
            'dia': fecha.strftime('%Y-%m-%d'),
            'total': 0 
        })
    
    return JsonResponse(datos, safe=False)