import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from botocore.config import Config
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import traceback
from django.db import connections
from django.conf import settings
from user.models import *
from .models import *
import boto3

import os

ORS_API_KEY = os.environ.get('ORS_API_KEY', '')
ORS_URL = os.environ.get('ORS_URL', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

def driver(request):
    

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM vehicles WHERE type = 'MOTORCYCLE' AND status = 'APPROVED'")
        moto_aprov = cursor.fetchone()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM vehicles WHERE type = 'CAR' AND status = 'APPROVED'")
        car_aprov = cursor.fetchone()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM vehicles WHERE type = 'CAR' AND status = 'APPROVED'")
        conduct_moto = cursor.fetchone()

    print('cantidad de moto aprobado', moto_aprov)
    print('cantidad de carro aprobado', car_aprov)


    context = {
        'moto_aprov': moto_aprov,
        'car_aprov': car_aprov,
        'is_admin': request.user.is_superuser
    }

    

    return render(request, 'driver/driver.html', context)

@csrf_exempt 
def lista_driver(request):
    
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.public_id,
                u.name,
                u.last_name,
                u.document,
                u.email,
                u.phone,
                u.deletion_status,
                u.created_at,
                u.status,
                u.deleted,
                d.id as driver_id,
                d.driver_status,
                d.working
            FROM users u
            INNER JOIN drivers d ON u.id = d.user_id
            WHERE u.deleted = false
            ORDER BY u.created_at DESC
        """)
        drivers = cursor.fetchall()
    
    data = []
    for driver in drivers:
        data.append({
            'id': driver[0],  
            'name': driver[1] or '',  
            'last_name': driver[2] or '',  
            'document': driver[3] or '',  
            'email': driver[4] or '',  
            'phone': driver[5] or '',
            'deletion_status': driver[6], 
            'created_at': driver[7].strftime('%Y-%m-%d %H:%M:%S') if driver[6] else '',
            'status': driver[8],  
            'deleted': driver[9],  
            'driver_id': driver[10],  
            'driver_status': driver[11], 
            'working': driver[12] 
        })
    
    # Agregar is_admin a la respuesta
    is_admin = request.user.is_staff or request.user.is_superuser
    
    return JsonResponse({
        'data': data,
        'is_admin': is_admin
    }, safe=False)


def driver_details(request, id):
    
    if 'legacy' not in connections.databases:
        db_alias = 'default'
        print("Conexión 'legacy' no encontrada, usando 'default'")
    else:
        db_alias = 'legacy'
    
    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.public_id,
                    u.name,
                    u.last_name,
                    u.document,
                    u.email,
                    u.phone,
                    u.created_at,
                    d.id as driver_id,
                    d.driver_status,
                    d.working
                FROM users u
                INNER JOIN drivers d ON u.id = d.user_id
                WHERE u.public_id = %s AND u.deleted = false
            """, [id])
            
            driver_data = cursor.fetchone()
            
            if not driver_data:
                return render(request, 'error.html', {'mensaje': 'Conductor no encontrado'})
            
            conductor_info = {
                'public_id': driver_data[0],
                'name': driver_data[1],
                'last_name': driver_data[2],
                'document': driver_data[3],
                'email': driver_data[4],
                'phone': driver_data[5] or '',
                'created_at': driver_data[6],
                'driver_status': driver_data[8],
                'working': driver_data[9],
            }
            
            context = {
                'conductor': conductor_info,
                'public_id': id,
            }
            
            return render(request, 'driver/drivers_details.html', context)
            
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'error.html', {'mensaje': f'Error: {str(e)}'})
    

def upload_to_cloudflare_r2(file, document_number):
    """
    Sube una imagen a Cloudflare R2
    """
    try:
        # VERIFICACIÓN EXPLÍCITA DE CADA VARIABLE
        print("🔍 Verificando configuración de R2:")
        
        # Verificar CLOUDFLARE_R2_KEY_ID
        key_id = getattr(settings, 'CLOUDFLARE_R2_KEY_ID', None)
        print(f"  - CLOUDFLARE_R2_KEY_ID: {'✅ Configurado' if key_id else '❌ FALTA'}")
        
        # Verificar CLOUDFLARE_R2_ACCESS_KEY
        access_key = getattr(settings, 'CLOUDFLARE_R2_ACCESS_KEY', None)
        print(f"  - CLOUDFLARE_R2_ACCESS_KEY: {'✅ Configurado' if access_key else '❌ FALTA'}")
        
        # Verificar CLOUDFLARE_R2_ENDPOINT
        endpoint = getattr(settings, 'CLOUDFLARE_R2_ENDPOINT', None)
        print(f"  - CLOUDFLARE_R2_ENDPOINT: {'✅ Configurado' if endpoint else '❌ FALTA'}")
        
        # Verificar CLOUDFLARE_R2_BUCKET
        bucket = getattr(settings, 'CLOUDFLARE_R2_BUCKET', None)
        print(f"  - CLOUDFLARE_R2_BUCKET: {'✅ Configurado' if bucket else '❌ FALTA'}")
        
        # Verificar CLOUDFLARE_R2_PUBLIC_URL
        public_url = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', None)
        print(f"  - CLOUDFLARE_R2_PUBLIC_URL: {'✅ Configurado' if public_url else '❌ FALTA'}")
        
        # Si alguna variable es None, lanzar error específico
        if not key_id:
            raise ValueError("❌ CLOUDFLARE_R2_KEY_ID no está configurado en settings.py")
        if not access_key:
            raise ValueError("❌ CLOUDFLARE_R2_ACCESS_KEY no está configurado en settings.py")
        if not endpoint:
            raise ValueError("❌ CLOUDFLARE_R2_ENDPOINT no está configurado en settings.py")
        if not bucket:
            raise ValueError("❌ CLOUDFLARE_R2_BUCKET no está configurado en settings.py")
        
        # Continuar con la subida...
        print("✅ Todas las configuraciones están presentes")
        
        # Resto de tu código aquí...
        session = boto3.session.Session()
        client = session.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=access_key,
            config=Config(signature_version='s3v4')
        )
        
        # Generar nombre del archivo
        file_extension = file.name.split('.')[-1].lower()
        new_filename = f"drivers-profiles/{document_number}.{file_extension}"
        
        # Resetear el puntero del archivo
        file.seek(0)
        
        print(f"📤 Subiendo archivo: {new_filename}")
        
        # Intentar subir con manejo específico de errores
        try:
            client.upload_fileobj(
                file,
                settings.CLOUDFLARE_R2_BUCKET,
                new_filename,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read'  # Esto requiere que el bucket permita ACLs
                }
            )
        except client.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'Unauthorized':
                raise Exception(f"❌ Credenciales inválidas o sin permisos de escritura. Verifica el Access Key y Secret Key")
            elif error_code == 'NoSuchBucket':
                raise Exception(f"❌ El bucket '{settings.CLOUDFLARE_R2_BUCKET}' no existe")
            else:
                raise Exception(f"❌ Error {error_code}: {str(e)}")
        
        # Generar URL pública
        file_url = f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{new_filename}"
        print(f"✅ Imagen subida exitosamente: {file_url}")
        
        return file_url
        
    except Exception as e:
        print(f"❌ Error subiendo a R2: {e}")
        raise
    

def upload_photo(request, id):
    # Verificar conexión legacy
    if 'legacy' not in connections.databases:
        db_alias = 'default'
        print("Conexión 'legacy' no encontrada, usando 'default'")
    else:
        db_alias = 'legacy'

    # Verificar que sea POST para procesar la imagen
    if request.method == 'POST':
        # Validar que exista el archivo
        if 'image' not in request.FILES:
            messages.error(request, 'No se seleccionó ninguna imagen')
            return redirect('upload_photo', id=id)
        
        image = request.FILES['image']

        file_extension = image.name.split('.')[-1].lower()
        
        # Validaciones del archivo
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image.content_type not in allowed_types:
            messages.error(request, 'Tipo de archivo no permitido. Use JPEG, PNG o WEBP')
            return redirect('upload_photo', id=id)
        
        if image.size > 5 * 1024 * 1024:  # 5MB máximo
            messages.error(request, 'La imagen no puede superar los 5MB')
            return redirect('upload_photo', id=id)
        
        try:
            with connections[db_alias].cursor() as cursor:
               
                cursor.execute("""
                    SELECT 
                        u.public_id,
                        u.name,
                        u.last_name,
                        u.document,
                        u.email,
                        u.phone,
                        u.created_at,
                        d.id as driver_id,
                        d.driver_status,
                        d.photo,
                        d.working
                    FROM users u
                    INNER JOIN drivers d ON u.id = d.user_id
                    WHERE u.public_id = %s AND u.deleted = false
                """, [id])
                
                driver_data = cursor.fetchone()
                
                if not driver_data:
                    return render(request, 'error.html', {'mensaje': 'Conductor no encontrado'})
                
                # Obtener el número de documento
                document = driver_data[3]  # u.document
                driver_id = driver_data[7]  

                # ========== PARTE CORREGIDA ==========
                # PRIMERO: Intentar subir la imagen a Cloudflare R2
                try:
                    # Subir imagen a Cloudflare R2
                    cloudflare_url = upload_to_cloudflare_r2(image, document)
                    

                    name_photo = f"{document}.{file_extension}"
                    
                    # SEGUNDO: Actualizar la base de datos con la URL de Cloudflare
                    cursor.execute("""
                        UPDATE drivers 
                        SET photo = %s 
                        WHERE id = %s
                    """, [name_photo, driver_id])  # Guardamos la URL completa
                    
                    print(f"Foto subida exitosamente a Cloudflare: {cloudflare_url}")
                    
                except Exception as cloudflare_error:
                    # Si falla la subida a Cloudflare, mostramos error y NO actualizamos la BD
                    error_msg = f"Error al subir la imagen a Cloudflare: {str(cloudflare_error)}"
                    print(error_msg)
                    messages.error(request, error_msg)
                    
                    # Hacemos rollback si es necesario
                    if connections[db_alias].vendor in ['postgresql', 'mysql']:
                        connections[db_alias].rollback()
                    
                    return redirect('upload_photo', id=id)
                # ========== FIN PARTE CORREGIDA ==========
                
                print(f"Driver ID: {driver_id}")
                # Commit explícito si es necesario
                if connections[db_alias].vendor == 'postgresql':
                    connections[db_alias].commit()
                
                messages.success(request, 'Foto subida exitosamente a Cloudflare R2')
                return redirect('driver')  
                
        except Exception as e:
            print(f"Error general: {e}")
            # Hacer rollback en caso de error
            if connections[db_alias].vendor in ['postgresql', 'mysql']:
                connections[db_alias].rollback()
            messages.error(request, f'Error al subir la foto: {str(e)}')
            return redirect('upload_photo', id=id)
    
    # Si es GET, mostrar el formulario (resto del código igual...)
    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.public_id,
                    u.name,
                    u.last_name,
                    u.document,
                    u.email,
                    u.phone,
                    u.created_at,
                    d.id as driver_id,
                    d.driver_status,
                    d.working,
                    d.photo  -- Incluir la foto actual si existe
                FROM users u
                INNER JOIN drivers d ON u.id = d.user_id
                WHERE u.public_id = %s AND u.deleted = false
            """, [id])
            
            driver_data = cursor.fetchone()
            
            if not driver_data:
                return render(request, 'error.html', {'mensaje': 'Conductor no encontrado'})
            
            conductor_info = {
                'public_id': driver_data[0],
                'name': driver_data[1],
                'last_name': driver_data[2],
                'document': driver_data[3],
                'email': driver_data[4],
                'phone': driver_data[5] or '',
                'created_at': driver_data[6],
                'driver_status': driver_data[8],
                'working': driver_data[9],
                'photo': driver_data[10] if len(driver_data) > 10 else None,
            }
            
            context = {
                'conductor': conductor_info,
                'public_id': id,
            }
            
            return render(request, 'driver/upload_photo_1.html', context)
    
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'error.html', {'mensaje': f'Error: {str(e)}'})


def active_driver(request, id):

    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT
                u.name,
                u.last_name,
                u.email,                   
                d.id 
            FROM drivers d 
            INNER JOIN users u ON d.user_id = u.id
            WHERE u.public_id = %s
        """, [id])
        
        result = cursor.fetchone()
        
        if not result:
            messages.error(request, f'No se encontró el conductor con public_id: {id}')
            return redirect('driver')
        
        driver_name = result[0]
        driver_lastname = result[1]
        driver_email = result[2]  #
        driver_id = result[3]
    
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            UPDATE drivers 
            SET driver_status = 'APPROVED' 
            WHERE id = %s
        """, [driver_id])  


    driv ={
        'nombre': driver_name,
        'apellido': driver_lastname,
        'correo': driver_email,
    }

    html_content = render_to_string('emails/email.html', {
        'user_name': driv['nombre']+f' '+ driv['apellido'],
        
    })

    mensaje = EmailMessage(
        subject='¡Bienvenido a Now!',
        body=html_content,           
        from_email=DEFAULT_FROM_EMAIL,
        to=[driv['correo']],       
    )

    mensaje.content_subtype = "html" 
    mensaje.send()

    
    print('public_id recibido:', id)
    print('driver_id actualizado:', driver_id)
    
    messages.success(request, f'Conductor Activado (ID: {driver_id})')
    return redirect('driver')


def movement_driver(request, id):
    if 'legacy' not in connections.databases:
        db_alias = 'default'
        print("Conexión 'legacy' no encontrada, usando 'default'")
    else:
        db_alias = 'legacy'

    if request.method == 'POST':
        believe = request.POST.get('believe')
        description = request.POST.get('description')
        movement = request.POST.get('movement_type')
        comision = request.POST.get('comi')
        
        if not believe or believe == '':
            messages.error(request, 'No introdujo ningún monto')
            return redirect('movement_driver', id=id)

        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                    public_id,
                    id,
                    name,
                    last_name,
                    document,
                    email
                FROM users
                WHERE public_id = %s 
                """, [id])

                user_data = cursor.fetchone()
                user_id = user_data[1]

                cursor.execute("SELECT public_id, id FROM drivers WHERE user_id = %s", [user_id])
                driver_data = cursor.fetchone()

                if not driver_data:
                    return render(request, 'error.html', {'mensaje': 'conductor no encontrado'})
                
                driver_id = driver_data[1]

                print(driver_id)
                
                mont = believe.replace(",", ".")
                mont_comi = comision.replace(",", ".")
                print(mont)

                # Consultar wallet
                cursor.execute("""
                    SELECT 
                        public_id,
                        id,
                        balance
                    FROM drivers_wallets
                    WHERE driver_id = %s 
                """, [driver_id])
                
                driver_wallet = cursor.fetchone()
                
                new_balance = None
                wallet_id = None
                status = None

                if movement == 'DEBIT':
                    transaction_type = 'DEBIT'
                    status = 'COMPLETED'
                    balance_wallet = driver_wallet[2]
                    wallet_id = driver_wallet[1]
                    new_balance = float(balance_wallet) - float(mont) 

                elif movement == 'CREDIT':
                    transaction_type = 'CREDIT'
                    status = 'COMPLETED'
                    balance_wallet = driver_wallet[2]
                    wallet_id = driver_wallet[1]
                    new_balance = float(mont) + float(balance_wallet)

                else:
                    messages.error(request, 'Tipo de movimiento no válido')
                    return redirect('movement_driver', id=id)

                if new_balance is None:
                    messages.error(request, 'Error al calcular el nuevo balance')
                    return redirect('movement_driver', id=id)

                
                # Actualizar balance
                cursor.execute("""
                    UPDATE drivers_wallets 
                    SET balance = %s 
                    WHERE id = %s
                """, [new_balance, wallet_id])  
                
                # Corregido: INSERT correcto
                cursor.execute("""
                    INSERT INTO drivers_wallets_transactions 
                    (description, amount, commission_amount, type, status, driver_wallet_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [description, mont, mont_comi, transaction_type, status, wallet_id])
                
                # Commit después de todas las operaciones
                connections[db_alias].commit()

                if movement == 'CREDIT':
                
                    print(f"Monto acreditado correctamente: {believe}")
                    messages.success(request, 'Monto acreditado a la billetera correctamente')

                elif movement == 'DEBIT':
                    print(f"Monto acreditado correctamente: {believe}")
                    messages.success(request, 'Monto debitado a la billetera correctamente')

                return redirect('driver')  
            
        except Exception as e:
            print(f"Error: {e}")
            connections[db_alias].rollback()  # Rollback general
            messages.error(request, f'Error al acreditar: {str(e)}')
            return redirect('movement_driver', id=id)
    
    # GET request
    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    public_id,
                    name,
                    last_name,
                    document,
                    email
                FROM users
                WHERE public_id = %s 
            """, [id])
            
            user_data = cursor.fetchone()
            
            if not user_data:
                return render(request, 'error.html', {'mensaje': 'Usuario no encontrado'})
            
            usuario_info = {
                'public_id': user_data[0],
                'name': user_data[1],
                'last_name': user_data[2],
                'document': user_data[3],
                'email': user_data[4],
            }
            
            context = {
                'usuario': usuario_info,
                'public_id': id,
            }
            
            return render(request, 'driver/transc_driver.html', context)
    
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'error.html', {'mensaje': f'Error: {str(e)}'})


def driv_car(request):

    return render(request, 'driver/driver_car.html')


def list_driv_aprv_car_pend(request):
    data = []
    
    try:
        # Verificar que la conexión existe
        if 'legacy' not in connections:
            return JsonResponse({'error': 'Conexión legacy no encontrada'}, status=500)
        
        with connections['legacy'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.public_id,
                    d.id,
                    d.driver_status,
                    d.photo,
                    u.name,
                    u.document,
                    u.phone,
                    v.plate,
                    v.status,
                    v.type
                FROM drivers d 
                INNER JOIN users u ON u.id = d.user_id
                INNER JOIN vehicles v ON v.driver_id = d.id
                ORDER BY v.created_at DESC
            """)
            driv_aprov = cursor.fetchall()
        
        print(f"Registros encontrados: {len(driv_aprov)}")  # Debug
        
        for driv in driv_aprov:
            # Asegurarse de que driv tiene suficientes elementos
            if len(driv) >= 9:
                data.append({
                    'public_id': driv[0] or '',  
                    'id': driv[1] or '',  
                    'driver_status': driv[2] or '',  
                    'photo': 'SI' if driv[3] and driv[3] != '' else 'NO',
                    'name': driv[4] or '',  
                    'document': driv[5] or '',  
                    'phone': str(driv[6] or ''),
                    'plate': driv[7] or '', 
                    'status': driv[8] or '',  
                    'type': {
                    'CAR': 'CARRO',
                    'VAN': 'VAN',
                    'MOTORCYCLE': 'MOTOCICLETA'
                    }.get(driv[9], ''),
                    
                })
            else:
                print(f"Error: tupla con longitud {len(driv)}: {driv}")
        
        return JsonResponse({'data': data}, safe=False)
        
    except Exception as e:
        print(f"Error en list_driv_aprv_car_pend: {str(e)}")
        print(traceback.format_exc())  # Imprime el stack trace completo
        # Siempre retornar un JsonResponse válido
        return JsonResponse({'error': str(e), 'data': []}, status=500)




#-------------------------maps ---------------------------------------

# # ============================================
# # CONEXIÓN A REDIS EN AWS EC2
# # ============================================
# print("\n" + "="*50)
# print("🔄 CONECTANDO A REDIS EN AWS")
# print("="*50)

# REDIS_CONNECTED = False
# redis_client = None

# try:
#     # Intentar conexión con los parámetros de settings
#     redis_client = redis.Redis(**settings.REDIS_CONFIG)
    
#     # Probar conexión
#     redis_client.ping()
#     REDIS_CONNECTED = True
    
#     print("✅ Conexión a Redis en AWS exitosa")
#     print(f"   Host: {settings.REDIS_CONFIG['host']}:{settings.REDIS_CONFIG['port']}")
#     print(f"   DB: {settings.REDIS_CONFIG.get('db', 0)}")
#     print(f"   Autenticación: {'Sí' if 'password' in settings.REDIS_CONFIG else 'No'}")
    
#     # Mostrar información de Redis
#     info = redis_client.info()
#     print(f"   Versión: {info.get('redis_version')}")
#     print(f"   Claves totales: {info.get('db0', {}).get('keys', 0)}")
#     print(f"   Uptime: {info.get('uptime_in_seconds')} segundos")
    
# except redis.exceptions.AuthenticationError as e:
#     print(f"❌ Error de autenticación: {e}")
#     print("\n📝 La conexión requiere autenticación.")
#     print("   Pregunta a tu amigo la contraseña de Redis")
    
# except redis.exceptions.ConnectionError as e:
#     print(f"❌ Error de conexión: {e}")
#     print("\n📝 Posibles causas:")
#     print("   1. El puerto 6379 no está abierto en el Security Group de AWS")
#     print("   2. La IP de tu máquina no está permitida en el Security Group")
#     print("   3. La instancia EC2 no está corriendo")
#     print("   4. Redis no está escuchando en la interfaz correcta")
#     print("   5. La IP o DNS es incorrecto")
    
# except Exception as e:
#     print(f"❌ Error inesperado: {e}")
#     import traceback
#     traceback.print_exc()

# print("="*50 + "\n")


# def mapa(request):
    
#     return render(request, 'maps/maps.html')

# def api_conductores(request):
#     """
#     API para obtener ubicación de conductores desde Redis en AWS
#     """
#     print("\n" + "="*50)
#     print("🔍 SOLICITUD A API DE CONDUCTORES")
#     print("="*50)
    
#     if not REDIS_CONNECTED:
#         print("❌ Redis NO está conectado")
#         return JsonResponse({'error': 'Redis no está conectado'}, status=500)
    
#     try:
#         # Obtener TODAS las claves
#         all_keys = redis_client.keys('*')
#         print(f"📌 Total de claves en Redis: {len(all_keys)}")
#         print(f"📌 Claves encontradas: {all_keys}")
        
#         conductores = []
        
#         for key in all_keys:
#             key_type = redis_client.type(key)
#             print(f"\n🔑 Clave: {key} (Tipo: {key_type})")
            
#             if key_type == 'hash':
#                 hash_data = redis_client.hgetall(key)
#                 print(f"📦 Datos del hash para {key}:")
#                 for field, value in hash_data.items():
#                     display_value = value[:100] + "..." if len(value) > 100 else value
#                     print(f"   - {field}: {display_value}")
                
#                 if 'coords' in hash_data:
#                     try:
#                         coords_data = json.loads(hash_data['coords'])
#                         print(f"📍 Coordenadas parseadas: {coords_data}")
                        
#                         conductor = {
#                             'id': key,
#                             'lat': float(coords_data.get('latitude', 0)),
#                             'lng': float(coords_data.get('longitude', 0)),
#                             'heading': coords_data.get('heading', 0),
#                             'status': hash_data.get('status', 'unknown'),
#                             'name': hash_data.get('name', 'Sin nombre'),
#                             'phone': hash_data.get('phone', ''),
#                             'vehicle': hash_data.get('vehicle', '')
#                         }
                        
#                         conductores.append(conductor)
#                         print(f"✅ Conductor agregado: {conductor['name']} - {conductor['lat']}, {conductor['lng']}")
                        
#                     except json.JSONDecodeError as e:
#                         print(f"❌ Error parseando coords para {key}: {e}")
#                         print(f"   Valor raw: {hash_data['coords']}")
#                 else:
#                     print(f"⚠️ La clave {key} no tiene campo 'coords'")
#                     print(f"   Campos disponibles: {list(hash_data.keys())}")
#             else:
#                 value = redis_client.get(key)
#                 print(f"📝 Valor para {key}: {value[:100] if value else 'None'}")
        
#         print(f"\n✅ Total conductores procesados: {len(conductores)}")
#         print("="*50 + "\n")
        
#         return JsonResponse({'conductores': conductores})
    
#     except Exception as e:
#         print(f"❌ ERROR: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return JsonResponse({'error': str(e)}, status=500)
    
# def api_ruta(request):
    
#     if request.method != 'GET':
#         return JsonResponse({'error': 'Método no permitido'}, status=405)
    
#     origen_lat = request.GET.get('origen_lat')
#     origen_lng = request.GET.get('origen_lng')
#     destino_lat = request.GET.get('destino_lat')
#     destino_lng = request.GET.get('destino_lng')
    
#     if not all([origen_lat, origen_lng, destino_lat, destino_lng]):
#         return JsonResponse({'error': 'Faltan coordenadas'}, status=400)
    
#     try:
#         # Construir la URL de la API de OpenRouteService
#         url = f"{ORS_URL}/directions/driving-car"
        
#         headers = {
#             'Authorization': ORS_API_KEY,
#             'Content-Type': 'application/json'
#         }
        
#         payload = {
#             'coordinates': [
#                 [float(origen_lng), float(origen_lat)],
#                 [float(destino_lng), float(destino_lat)]
#             ],
#             'geometry': True,
#             'instructions': True
#         }
        
#         response = requests.post(url, json=payload, headers=headers)
        
#         if response.status_code == 200:
#             data = response.json()
            
#             # Extraer la geometría de la ruta
#             if 'features' in data and len(data['features']) > 0:
#                 geometry = data['features'][0]['geometry']['coordinates']
#                 # Convertir a formato [lat, lng] para Leaflet
#                 ruta = [[coord[1], coord[0]] for coord in geometry]
                
#                 # Extraer información de la ruta
#                 summary = data['features'][0]['properties']['summary']
#                 distancia_km = summary['distance'] / 1000  # Convertir a kilómetros
#                 duracion_min = summary['duration'] / 60    # Convertir a minutos
                
#                 return JsonResponse({
#                     'ruta': ruta,
#                     'distancia': round(distancia_km, 2),
#                     'duracion': round(duracion_min, 2)
#                 })
        
#         return JsonResponse({'error': 'No se pudo calcular la ruta'}, status=500)
    
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)