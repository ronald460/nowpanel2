from rest_framework import serializers
from .models import Email, EmailLabel

class EmailSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Email"""
    sender_name = serializers.SerializerMethodField()
    recipients_display = serializers.SerializerMethodField()
    labels = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        read_only=True
    )
    
    class Meta:
        model = Email
        fields = [
            'id', 'user', 'subject', 'sender', 'sender_name',
            'recipients', 'recipients_display', 'cc', 'bcc',
            'body_text', 'body_html', 'sent_at', 'is_read',
            'is_archived', 'is_trash', 'is_draft', 'is_sent',
            'attachments', 'labels', 'summary', 'message_id'
        ]
        read_only_fields = ['id', 'user', 'sent_at']
    
    def get_sender_name(self, obj):
        """Extraer nombre del remitente"""
        if '<' in obj.sender:
            return obj.sender.split('<')[0].strip()
        return obj.sender
    
    def get_recipients_display(self, obj):
        """Mostrar destinatarios de forma legible"""
        return ', '.join(obj.recipients) if obj.recipients else ''

class EmailLabelSerializer(serializers.ModelSerializer):
    """Serializer para el modelo EmailLabel"""
    email_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailLabel
        fields = ['id', 'name', 'color', 'emails', 'email_count']
        read_only_fields = ['id', 'user']
    
    def get_email_count(self, obj):
        """Obtener el número de correos con esta etiqueta"""
        return obj.emails.count()