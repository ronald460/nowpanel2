import json
import xlsxwriter
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
import pytz
from datetime import datetime, timedelta


def viajes(request):

    context = {
        'is_admin': request.user.is_superuser
    }


    return render(request, 'travel/travel.html', context)


def lista_travels(request):
    
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
                        SELECT 
                            t.public_id,
                            t.id,
                            t.distance,
                            t.duration,
                            t.status,     
                            t.type,
                            t.created_at,
                            u.name AS driver_name,    
                            u.phone,                  
                            u2.name AS user_name
                                
                        FROM travels t 
                        LEFT JOIN drivers d ON t.driver_id = d.id
                        LEFT JOIN users u ON d.user_id = u.id    
                        LEFT JOIN users u2 ON t.user_id = u2.id
                        
                        ORDER BY created_at DESC
                    """)
        travel = cursor.fetchall()
    
    # Zona horaria de Venezuela
    venezuela_tz = pytz.timezone('America/Caracas')
    
    data = []
    for trav in travel:
        # Convertir a zona horaria de Venezuela si existe
        created_at = trav[6]
        if created_at:
            # Si es naive (sin zona horaria), asumir UTC
            if created_at.tzinfo is None:
                created_at = pytz.UTC.localize(created_at)
            # Convertir a zona horaria de Venezuela
            created_at_venezuela = created_at.astimezone(venezuela_tz)
            created_at_str = created_at_venezuela.strftime('%d/%m/%Y-%I:%M %p')
        else:
            created_at_str = ''
        
        data.append({
            'public_id': trav[0],  
            'id': trav[1] or '',  
            'distance': trav[2] or '',  
            'duration': trav[3] or '',  
            'status': trav[4] or '',  
            'type': trav[5] or '',
            'created_at': created_at_str,
            'd_name': trav[7] or '',
            'd_phone': trav[8] or '',
            'u_name': trav[9] or '',
        })
    
    return JsonResponse({'data': data}, safe=False)


def details_travel(request, id):
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT
                u.public_id AS user_public_id,
                u.name AS user_name,
                u.last_name AS user_last_name,
                u.document AS user_document,
                u.phone AS user_phone,
                u2.name AS driver_name,
                u2.last_name AS driver_last_name,
                u2.document AS driver_document,
                u2.phone AS driver_phone,
                d.public_id AS driver_public_id,
                t.public_id,
                t.origin_address,
                t.dest_address,
                t.distance,
                t.duration,
                t.status,     
                t.created_at,
                t.updated_at   
            FROM travels t 
            LEFT JOIN drivers d ON t.driver_id = d.id
            LEFT JOIN users u ON d.user_id = u.id    
            LEFT JOIN users u2 ON t.user_id = u2.id
            WHERE t.public_id = %s
        """, [id])
        
        travel = cursor.fetchone()  # Cambiado a fetchone()
        
        # Manejar caso donde no se encuentra el viaje
        if not travel:
            # Podrías redirigir o mostrar un error 404
            return render(request, 'travel/not_found.html', {'message': 'Viaje no encontrado'})

    venezuela_tz = pytz.timezone('America/Caracas')

    # Ahora los índices son correctos
    created_at = travel[16]  # created_at
    updated_at = travel[17]  # updated_at
    
    created_at_str = ''
    if created_at:
        if created_at.tzinfo is None:
            created_at = pytz.UTC.localize(created_at)
        created_at_venezuela = created_at.astimezone(venezuela_tz)
        created_at_str = created_at_venezuela.strftime('%d/%m/%Y-%I:%M %p')

    updated_at_str = ''
    if updated_at:
        if updated_at.tzinfo is None:
            updated_at = pytz.UTC.localize(updated_at)
        updated_at_venezuela = updated_at.astimezone(venezuela_tz)
        updated_at_str = updated_at_venezuela.strftime('%d/%m/%Y-%I:%M %p')

    datos = {
        'user_public_id': travel[0],
        'user_name': travel[1],
        'user_last_name': travel[2],
        'user_document': travel[3],
        'user_phone': travel[4],
        'driver_name': travel[5],
        'driver_last_name': travel[6],
        'driver_document': travel[7],
        'driver_phone': travel[8],
        'driver_public_id': travel[9],
        'public_id': travel[10],
        'origin_address': travel[11],
        'dest_address': travel[12],
        'distance': travel[13],
        'duration': travel[14],
        'status': travel[15],
        'created_at': created_at_str,
        'updated_at': updated_at_str,
        'is_admin':request.user.is_superuser,
    }

    return render(request, 'travel/details.html', datos)

def report_travels(request):
    # Obtener la fecha de ayer en zona horaria de Venezuela
    venezuela_tz = pytz.timezone('America/Caracas')
    today = datetime.now(venezuela_tz)
    yesterday = today - timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    with connections['legacy'].cursor() as cursor:
        # Consulta principal - obtener todos los viajes de ayer con el documento del usuario
        cursor.execute("""
            SELECT 
                t.id,
                t.public_id,
                t.user_id,
                t.driver_id,
                t.status,
                t.type,
                t.created_at,
                u.name AS user_name,
                u.phone AS user_phone,
                u.document AS user_document,
                u2.name AS driver_name,
                u2.phone AS driver_phone
            FROM travels t
            LEFT JOIN drivers d ON t.driver_id = d.id
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN users u2 ON d.user_id = u2.id
            WHERE t.created_at BETWEEN %s AND %s
            ORDER BY t.created_at DESC
        """, [yesterday_start, yesterday_end])
        
        travels = cursor.fetchall()
        
        # Obtener TODOS los viajes completados del día anterior con su hora y documento
        cursor.execute("""
            SELECT 
                u.document,
                DATE(t.created_at) as fecha,
                EXTRACT(HOUR FROM t.created_at) as hora,
                t.type,
                COUNT(*) as total_completados
            FROM travels t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.status = 'COMPLETED'
            AND t.created_at BETWEEN %s AND %s
            GROUP BY u.document, DATE(t.created_at), EXTRACT(HOUR FROM t.created_at), t.type
        """, [yesterday_start, yesterday_end])
        
        completed_by_hour = {}
        for row in cursor.fetchall():
            document = row[0] or ''
            fecha = row[1]
            hora = row[2]
            tipo = row[3]
            key = f"{document}_{fecha}_{int(hora)}_{tipo}"
            completed_by_hour[key] = row[4]
        
        # Obtener todas las solicitudes que fueron aceptadas (no importa si se completaron o no)
        cursor.execute("""
            SELECT 
                u.document,
                DATE(t.created_at) as fecha,
                EXTRACT(HOUR FROM t.created_at) as hora,
                t.type,
                COUNT(*) as total_aceptadas
            FROM travels t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.status IN ('DRIVER_ACCEPTED', 'IN_PROGRESS', 'COMPLETED')
            AND t.created_at BETWEEN %s AND %s
            GROUP BY u.document, DATE(t.created_at), EXTRACT(HOUR FROM t.created_at), t.type
        """, [yesterday_start, yesterday_end])
        
        accepted_by_hour = {}
        for row in cursor.fetchall():
            document = row[0] or ''
            fecha = row[1]
            hora = row[2]
            tipo = row[3]
            key = f"{document}_{fecha}_{int(hora)}_{tipo}"
            accepted_by_hour[key] = row[4]
    
    # Diccionarios para almacenar los conteos por tipo de vehículo
    completed_counts = {}
    cancelled_counts = {}
    total_requests = {}
    
    # Conjunto para rastrear viajes que ya fueron contados como cancelados
    counted_cancelled = set()
    # Diccionario para rastrear cancelaciones por hora y documento
    hourly_cancellations = {}
    
    # Procesar cada viaje
    for trav in travels:
        travel_id = trav[0]
        public_id = trav[1]
        user_id = trav[2]
        driver_id = trav[3]
        status = trav[4]
        vehicle_type = trav[5] or 'No especificado'
        created_at = trav[6]
        user_name = trav[7] or ''
        user_phone = trav[8] or ''
        user_document = trav[9] or ''
        driver_name = trav[10] or ''
        driver_phone = trav[11] or ''
        
        # Inicializar contadores para el tipo de vehículo
        if vehicle_type not in completed_counts:
            completed_counts[vehicle_type] = 0
            cancelled_counts[vehicle_type] = 0
            total_requests[vehicle_type] = 0
        
        # Contar todas las solicitudes por tipo de vehículo
        total_requests[vehicle_type] += 1
        
        # PROCESAR VIAJES COMPLETADOS
        if status == 'COMPLETED':
            completed_counts[vehicle_type] += 1
        
        # PROCESAR VIAJES CANCELADOS CON LOS FILTROS ESPECIFICADOS
        elif status in ['CANCELLED', 'NO_SHOW', 'REJECTED', 'EXPIRED']:
            # Crear clave única para este viaje
            trip_key = f"{public_id}_{user_document}"
            
            # Verificar si este viaje ya fue contado como cancelado
            if trip_key not in counted_cancelled:
                # Obtener la hora del viaje
                hour = created_at.hour
                date_key = created_at.date()
                
                # FILTRO 1: Verificar si en la MISMA HORA hay un viaje completado para este documento
                completed_key = f"{user_document}_{date_key}_{hour}_{vehicle_type}"
                has_completed_in_hour = completed_by_hour.get(completed_key, 0) > 0
                
                # FILTRO 2: Verificar si en la MISMA HORA hay un viaje aceptado para este documento
                accepted_key = f"{user_document}_{date_key}_{hour}_{vehicle_type}"
                has_accepted_in_hour = accepted_by_hour.get(accepted_key, 0) > 0
                
                # REGLA 1: Si hay un viaje completado en la misma hora, NO contar esta cancelación
                # (el usuario logró hacer el viaje, las cancelaciones previas no cuentan)
                if has_completed_in_hour:
                    continue
                
                # REGLA 2: Si hay múltiples solicitudes en la misma hora sin aceptación
                # Contar SOLO UNA cancelación por hora
                cancel_hour_key = f"{user_document}_{date_key}_{hour}_{vehicle_type}"
                
                # Verificar si es la primera cancelación de esta hora para este usuario
                if cancel_hour_key not in hourly_cancellations:
                    # Solo contar si NO hay viajes aceptados en esa hora
                    if not has_accepted_in_hour:
                        cancelled_counts[vehicle_type] += 1
                        hourly_cancellations[cancel_hour_key] = True
                        counted_cancelled.add(trip_key)
                else:
                    # Ya se contó una cancelación para esta hora, no contar más
                    counted_cancelled.add(trip_key)
    
    # Preparar datos para el reporte
    report_data = []
    total_completed = 0
    total_cancelled = 0
    total_requests_count = 0
    
    for vehicle_type in total_requests.keys():
        completed = completed_counts.get(vehicle_type, 0)
        cancelled = cancelled_counts.get(vehicle_type, 0)
        total = total_requests.get(vehicle_type, 0)
        
        report_data.append({
            'tipo_vehiculo': vehicle_type,
            'viajes_completados': completed,
            'viajes_cancelados': cancelled,
            'total_solicitudes': total,
            'porcentaje_cancelacion': round((cancelled / total * 100) if total > 0 else 0, 2)
        })
        
        total_completed += completed
        total_cancelled += cancelled
        total_requests_count += total
    
    # Agregar totales generales
    report_data.append({
        'tipo_vehiculo': 'TOTAL GENERAL',
        'viajes_completados': total_completed,
        'viajes_cancelados': total_cancelled,
        'total_solicitudes': total_requests_count,
        'porcentaje_cancelacion': round((total_cancelled / total_requests_count * 100) if total_requests_count > 0 else 0, 2)
    })
    
    response = {
        'fecha_reporte': yesterday.strftime('%d/%m/%Y'),
        'datos': report_data,
        'resumen': {
            'total_completados': total_completed,
            'total_cancelados': total_cancelled,
            'total_solicitudes': total_requests_count,
            'tasa_cancelacion': round((total_cancelled / total_requests_count * 100) if total_requests_count > 0 else 0, 2)
        }
    }
    
    return JsonResponse(response, safe=False)


def export_excel_report(request):
    # Obtener los datos del reporte
    report_response = report_travels(request)
    report_data = json.loads(report_response.content)
    
    # Crear el archivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=reporte_viajes_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet('Reporte Diario')
    
    # Formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4CAF50',
        'color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center'
    })
    
    percentage_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'num_format': '0.00'
    })
    
    total_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'bg_color': '#E6E6E6'
    })
    
    # Encabezados
    headers = ['Tipo de Vehículo', 'Viajes Completados', 'Viajes Cancelados', 
               'Total Solicitudes', '% Cancelación']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Escribir datos
    row = 1
    for data in report_data['datos']:
        if data['tipo_vehiculo'] == 'TOTAL GENERAL':
            worksheet.write(row, 0, data['tipo_vehiculo'], total_format)
            worksheet.write(row, 1, data['viajes_completados'], total_format)
            worksheet.write(row, 2, data['viajes_cancelados'], total_format)
            worksheet.write(row, 3, data['total_solicitudes'], total_format)
            worksheet.write(row, 4, data['porcentaje_cancelacion'], total_format)
        else:
            worksheet.write(row, 0, data['tipo_vehiculo'], cell_format)
            worksheet.write(row, 1, data['viajes_completados'], cell_format)
            worksheet.write(row, 2, data['viajes_cancelados'], cell_format)
            worksheet.write(row, 3, data['total_solicitudes'], cell_format)
            worksheet.write(row, 4, data['porcentaje_cancelacion'], percentage_format)
        row += 1
    
    # Agregar resumen adicional
    row += 2
    worksheet.write(row, 0, 'RESUMEN EJECUTIVO', header_format)
    row += 1
    worksheet.write(row, 0, 'Fecha del Reporte:', cell_format)
    worksheet.write(row, 1, report_data['fecha_reporte'], cell_format)
    row += 1
    worksheet.write(row, 0, 'Total Viajes Completados:', cell_format)
    worksheet.write(row, 1, report_data['resumen']['total_completados'], cell_format)
    row += 1
    worksheet.write(row, 0, 'Total Viajes Cancelados:', cell_format)
    worksheet.write(row, 1, report_data['resumen']['total_cancelados'], cell_format)
    row += 1
    worksheet.write(row, 0, 'Tasa de Cancelación General:', cell_format)
    worksheet.write(row, 1, f"{report_data['resumen']['tasa_cancelacion']}%", cell_format)
    
    # Ajustar ancho de columnas
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:E', 20)
    
    workbook.close()
    return response