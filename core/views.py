from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
from .models import Email
import requests
import logging
import hashlib
import hmac
import json

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


def obtener_contenido_completo(email_id):
    """Obtiene el contenido completo de un correo desde Resend"""
    try:
        api_key = settings.ANYMAIL.get('RESEND_API_KEY')
        url = f"https://api.resend.com/emails/{email_id}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Contenido obtenido para email: {email_id}")
            return data
        else:
            logger.error(f"❌ Error obteniendo contenido: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error en petición a Resend: {str(e)}")
        return None

@csrf_exempt
def resend_webhook(request):
    """Maneja los webhooks de Resend para correos entrantes"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        logger.info(f"📨 Webhook recibido: {data}")
        
        # Verificar la firma (si hay secret configurado)
        webhook_secret = getattr(settings, 'RESEND_WEBHOOK_SECRET', '')
        if webhook_secret:
            signature = request.headers.get('Resend-Signature')
            if signature:
                expected_signature = hmac.new(
                    webhook_secret.encode(),
                    request.body,
                    hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(signature, expected_signature):
                    logger.warning("⚠️ Firma inválida en el webhook")
                    return JsonResponse({'error': 'Firma inválida'}, status=401)
        
        # Procesar solo eventos de correo recibido
        event_type = data.get('type')
        if event_type != 'email.received':
            return JsonResponse({'status': 'ignored'}, status=200)
        
        email_data = data.get('data', {})
        email_id = email_data.get('email_id')
        
        if not email_id:
            logger.error("❌ No se encontró email_id en el webhook")
            return JsonResponse({'error': 'Falta email_id'}, status=400)
        
        # 🔥 Obtener el contenido completo del correo
        contenido_completo = obtener_contenido_completo(email_id)
        
        if contenido_completo:
            # Extraer el cuerpo del correo
            body_text = contenido_completo.get('text', '')
            body_html = contenido_completo.get('html', '')
            
            # Si no hay cuerpo, usar el que vino en el webhook (si existe)
            if not body_text and not body_html:
                body_text = email_data.get('text', '')
                body_html = email_data.get('html', '')
            
            # Guardar el correo con el contenido completo
            procesar_correo_completo(email_data, body_text, body_html, contenido_completo)
        else:
            # Si no se pudo obtener el contenido, guardar lo que tenemos
            logger.warning("⚠️ No se pudo obtener contenido completo, guardando solo metadatos")
            procesar_correo_completo(email_data, '', '', None)
        
        return JsonResponse({'status': 'success'}, status=200)
        
    except json.JSONDecodeError:
        logger.error("❌ Error: JSON inválido")
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def procesar_correo_completo(email_data, body_text, body_html, contenido_completo):
    """Procesa el correo con contenido completo"""
    try:
        sender_email = email_data.get('from', '')
        subject = email_data.get('subject', '')
        recipients = email_data.get('to', [])
        message_id = email_data.get('message_id', '')
        email_id = email_data.get('email_id', '')
        
        logger.info(f"📧 Correo recibido de: {sender_email}")
        logger.info(f"Asunto: {subject}")
        logger.info(f"Email ID: {email_id}")
        
        # Buscar al usuario destinatario
        user = None
        received_for = email_data.get('received_for', [])
        
        if received_for:
            for recipient in received_for:
                try:
                    user = User.objects.get(email=recipient)
                    break
                except User.DoesNotExist:
                    continue
        
        if not user:
            # Intentar con los destinatarios normales
            if recipients:
                for recipient in recipients:
                    try:
                        user = User.objects.get(email=recipient)
                        break
                    except User.DoesNotExist:
                        continue
        
        if not user:
            logger.warning(f"⚠️ No se encontró usuario para: {recipients}")
            return
        
        # Guardar el correo en la base de datos
        email = Email.objects.create(
            user=user,
            subject=subject or '',
            sender=sender_email,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body_text=body_text or '',
            body_html=body_html or '',
            is_sent=False,
            message_id=message_id,
            # Guardar el email_id de Resend para referencia futura
            # Si tu modelo tiene un campo para esto, guárdalo
        )
        
        logger.info(f"✅ Correo guardado con ID: {email.id}")
        logger.info(f"📝 Body text: {body_text[:100]}..." if body_text else "📝 Sin body text")
        
    except Exception as e:
        logger.error(f"❌ Error guardando correo: {str(e)}")
        raise