from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Email
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Vistas para las páginas principales
@login_required
def inbox_view(request):
    """Vista de la bandeja de entrada"""
    return render(request, 'core/inbox.html', {
        'section': 'inbox',
        'title': 'Bandeja de entrada'
    })

@login_required
def sent_view(request):
    """Vista de correos enviados"""
    return render(request, 'core/inbox.html', {
        'section': 'sent',
        'title': 'Correos enviados'
    })

@login_required
def drafts_view(request):
    """Vista de borradores"""
    return render(request, 'core/inbox.html', {
        'section': 'drafts',
        'title': 'Borradores'
    })

@login_required
def archived_view(request):
    """Vista de correos archivados"""
    return render(request, 'core/inbox.html', {
        'section': 'archived',
        'title': 'Archivados'
    })

@login_required
def trash_view(request):
    """Vista de la papelera"""
    return render(request, 'core/inbox.html', {
        'section': 'trash',
        'title': 'Papelera'
    })

@login_required
def starred_view(request):
    """Vista de correos destacados"""
    return render(request, 'core/inbox.html', {
        'section': 'starred',
        'title': 'Destacados'
    })

@login_required
def email_detail_view(request, pk):
    """Vista detalle de un correo"""
    email = get_object_or_404(Email, id=pk, user=request.user)
    return render(request, 'core/email_detail.html', {
        'email': email,
        'section': 'detail'
    })

@login_required
def compose_view(request):
    """Vista para redactar un correo"""
    return render(request, 'core/compose.html', {
        'section': 'compose'
    })

# Vistas para manejar acciones específicas
@login_required
@require_http_methods(["POST"])
def mark_as_read(request):
    """Marcar un correo como leído"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_read = True
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Marcado como leído'})

@login_required
@require_http_methods(["POST"])
def mark_as_unread(request):
    """Marcar un correo como no leído"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_read = False
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Marcado como no leído'})

@login_required
@require_http_methods(["POST"])
def archive_email(request):
    """Archivar un correo"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_archived = True
    email.is_trash = False
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Correo archivado'})

@login_required
@require_http_methods(["POST"])
def unarchive_email(request):
    """Desarchivar un correo"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_archived = False
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Correo desarchivado'})

@login_required
@require_http_methods(["POST"])
def delete_email(request):
    """Mover un correo a la papelera"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_trash = True
    email.is_archived = False
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Correo movido a la papelera'})

@login_required
@require_http_methods(["POST"])
def restore_email(request):
    """Restaurar un correo de la papelera"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_trash = False
    email.save()
    return JsonResponse({'status': 'success', 'message': 'Correo restaurado'})

@login_required
@require_http_methods(["POST"])
def permanent_delete_email(request):
    """Eliminar permanentemente un correo"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.delete()
    return JsonResponse({'status': 'success', 'message': 'Correo eliminado permanentemente'})

@login_required
@require_http_methods(["POST"])
def toggle_star(request):
    """Marcar/Desmarcar como destacado"""
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email = get_object_or_404(Email, id=email_id, user=request.user)
    email.is_starred = not email.is_starred
    email.save()
    return JsonResponse({
        'status': 'success', 
        'is_starred': email.is_starred,
        'message': 'Destacado actualizado'
    })

# Vista para obtener el conteo de correos no leídos
@login_required
def unread_count(request):
    """Obtener el número de correos no leídos"""
    count = Email.objects.filter(
        user=request.user,
        is_read=False,
        is_sent=False,
        is_trash=False,
        is_archived=False,
        is_draft=False
    ).count()
    return JsonResponse({'unread_count': count})

@csrf_exempt
def resend_webhook(request):
    """Maneja los webhooks de Resend para correos entrantes"""
    
    # Verificar que sea una petición POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener los datos del webhook
        data = json.loads(request.body)
        logger.info(f"📨 Webhook recibido: {data}")
        
        # Verificar el secret (opcional pero recomendado)
        webhook_secret = settings.ANYMAIL.get('RESEND_INBOUND_SECRET')
        if webhook_secret:
            signature = request.headers.get('Resend-Signature')
            # Si tienes el secret, verifica la firma aquí
            # Por ahora lo dejamos sin verificar para pruebas
        
        # Verificar que sea un evento de correo recibido
        event_type = data.get('type')
        if event_type != 'email.received':
            logger.info(f"Evento ignorado: {event_type}")
            return JsonResponse({'status': 'ignored'}, status=200)
        
        # Extraer los datos del correo
        email_data = data.get('data', {})
        
        # Procesar el correo
        procesar_correo_webhook(email_data)
        
        return JsonResponse({'status': 'success'}, status=200)
        
    except json.JSONDecodeError:
        logger.error("❌ Error: JSON inválido")
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def procesar_correo_webhook(email_data):
    """Procesa los datos del correo recibido"""
    try:
        # Extraer datos
        sender_email = email_data.get('from', '')
        subject = email_data.get('subject', '')
        recipients = email_data.get('to', [])
        body_text = email_data.get('text', '')
        body_html = email_data.get('html', '')
        message_id = email_data.get('id', '')
        
        logger.info(f"📧 Correo recibido de: {sender_email}")
        logger.info(f"Asunto: {subject}")
        
        # Buscar al usuario destinatario
        from django.contrib.auth.models import User
        
        # Si hay múltiples destinatarios, buscar el primero que coincida con un usuario
        user = None
        if recipients:
            if isinstance(recipients, list):
                for recipient in recipients:
                    try:
                        user = User.objects.get(email=recipient)
                        break
                    except User.DoesNotExist:
                        continue
            else:
                try:
                    user = User.objects.get(email=recipients)
                except User.DoesNotExist:
                    pass
        
        if not user:
            logger.warning(f"⚠️ No se encontró usuario para: {recipients}")
            return
        
        # Guardar el correo en la base de datos
        from .models import Email
        
        email = Email.objects.create(
            user=user,
            subject=subject or '',
            sender=sender_email,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body_text=body_text or '',
            body_html=body_html or '',
            is_sent=False,
            message_id=message_id,
        )
        
        logger.info(f"✅ Correo guardado con ID: {email.id}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando correo: {str(e)}")
        raise