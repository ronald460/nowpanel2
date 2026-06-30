from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Email, EmailLabel
from django.contrib.auth.models import User
import json

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