from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Email(models.Model):
    """Modelo principal para almacenar todos los correos"""
    
    # Relaciones
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    
    # Datos del correo
    subject = models.CharField(max_length=255, blank=True)
    sender = models.EmailField()
    recipients = models.JSONField(default=list)  # Lista de destinatarios
    cc = models.JSONField(default=list, blank=True)
    bcc = models.JSONField(default=list, blank=True)
    
    # Contenido
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    
    # Metadatos
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_trash = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)  # Nuevo campo
    
    # Identificadores externos
    message_id = models.CharField(max_length=255, blank=True)
    in_reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Adjuntos (metadatos)
    attachments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'is_trash']),
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'is_sent']),
            models.Index(fields=['user', 'is_starred']),
        ]
    
    def __str__(self):
        return f"{self.subject or 'Sin asunto'} - {self.sender}"
    
    @property
    def is_inbox(self):
        """Verifica si el correo está en la bandeja de entrada"""
        return (not self.is_sent and 
                not self.is_archived and 
                not self.is_trash and 
                not self.is_draft)
    
    @property
    def summary(self):
        """Resumen del cuerpo del correo (primeros 100 caracteres)"""
        text = self.body_text or self.body_html
        if text:
            # Eliminar etiquetas HTML si existen
            import re
            text = re.sub(r'<[^>]+>', '', text)
            return text[:100] + '...' if len(text) > 100 else text
        return ''

class EmailLabel(models.Model):
    """Etiquetas para organizar correos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4285f4')  # Color hexadecimal
    emails = models.ManyToManyField(Email, related_name='labels', blank=True)
    
    class Meta:
        unique_together = ['user', 'name']  # Un usuario no puede tener dos etiquetas con el mismo nombre
    
    def __str__(self):
        return self.name