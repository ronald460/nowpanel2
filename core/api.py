from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
import traceback
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Email, EmailLabel
from .serializers import EmailSerializer, EmailLabelSerializer
from anymail.signals import inbound
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

class EmailViewSet(viewsets.ModelViewSet):
    """API para gestionar correos"""
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar correos del usuario autenticado"""
        return Email.objects.filter(user=self.request.user).order_by('-sent_at')
    
    def perform_create(self, serializer):
        """Crear un nuevo correo (borrador o enviado)"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Obtener correos de la bandeja de entrada"""
        emails = self.get_queryset().filter(
            is_sent=False,
            is_archived=False,
            is_trash=False,
            is_draft=False
        )
        serializer = self.get_serializer(emails, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Obtener correos enviados"""
        emails = self.get_queryset().filter(
            is_sent=True,
            is_trash=False
        )
        serializer = self.get_serializer(emails, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def drafts(self, request):
        """Obtener borradores"""
        emails = self.get_queryset().filter(is_draft=True)
        serializer = self.get_serializer(emails, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Obtener correos archivados"""
        emails = self.get_queryset().filter(
            is_archived=True,
            is_trash=False
        )
        serializer = self.get_serializer(emails, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """Obtener correos en la papelera"""
        emails = self.get_queryset().filter(is_trash=True)
        serializer = self.get_serializer(emails, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archivar un correo"""
        email = self.get_object()
        email.is_archived = True
        email.is_trash = False
        email.save()
        return Response({'status': 'archived'})
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Desarchivar un correo"""
        email = self.get_object()
        email.is_archived = False
        email.save()
        return Response({'status': 'unarchived'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marcar como leído"""
        email = self.get_object()
        email.is_read = True
        email.save()
        return Response({'status': 'read'})
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Marcar como no leído"""
        email = self.get_object()
        email.is_read = False
        email.save()
        return Response({'status': 'unread'})
    
    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """Mover a la papelera"""
        email = self.get_object()
        email.is_trash = True
        email.save()
        return Response({'status': 'deleted'})
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaurar de la papelera"""
        email = self.get_object()
        email.is_trash = False
        email.save()
        return Response({'status': 'restored'})
    
    @action(detail=True, methods=['post'])
    def permanent_delete(self, request, pk=None):
        """Eliminar permanentemente"""
        email = self.get_object()
        email.delete()
        return Response({'status': 'permanently_deleted'})
    
    @action(detail=True, methods=['post'])
    def toggle_star(self, request, pk=None):
        """Marcar/Desmarcar como destacado"""
        email = self.get_object()
        # Asumiendo que tienes un campo 'is_starred' en el modelo
        # Si no lo tienes, puedes agregarlo o usar labels
        email.is_starred = not getattr(email, 'is_starred', False)
        email.save()
        return Response({'status': 'starred', 'is_starred': email.is_starred})
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Enviar un nuevo correo"""
        logger.info("="*50)
        logger.info("INICIANDO ENVÍO DE CORREO DESDE EL NAVEGADOR")
        logger.info(f"Usuario: {request.user.username} (ID: {request.user.id})")
        logger.info(f"Email del usuario: {request.user.email}")
        
        try:
            data = request.data
            logger.info(f"Datos recibidos: {data}")
            
            # Verificar que hay destinatarios
            if not data.get('recipients'):
                logger.error("ERROR: No se especificaron destinatarios")
                return Response({
                    'status': 'error',
                    'message': 'Debes especificar al menos un destinatario'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar que el usuario tiene email
            if not request.user.email:
                logger.error(f"ERROR: El usuario {request.user.username} no tiene email configurado")
                return Response({
                    'status': 'error',
                    'message': 'Tu usuario no tiene un email configurado. Contacta al administrador.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Determinar el remitente
            from_email = settings.DEFAULT_FROM_EMAIL
            logger.info(f"Remitente (from_email): {from_email}")
            logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            # Crear el email en la base de datos
            email = Email.objects.create(
                user=request.user,
                subject=data.get('subject', ''),
                sender=from_email,
                recipients=data.get('recipients', []),
                cc=data.get('cc', []),
                bcc=data.get('bcc', []),
                body_text=data.get('body_text', ''),
                body_html=data.get('emails/bienvenida.html', ''),
                is_sent=True
            )
            logger.info(f"Email creado en BD con ID: {email.id}")
            
            # Enviar el correo usando Resend
            try:
                logger.info("Intentando enviar correo con send_mail...")
                logger.info(f"Subject: {email.subject}")
                logger.info(f"Recipients: {email.recipients}")
                logger.info(f"From: {from_email}")
                
                result = send_mail(
                    subject=email.subject,
                    message=email.body_text or " ",
                    from_email=from_email,
                    recipient_list=email.recipients,
                    html_message=email.body_html or "",
                    fail_silently=False
                )
                
                logger.info(f"send_mail resultado: {result}")
                
                # Actualizar el estado del correo
                email.is_sent = True
                email.save()
                logger.info("✅ CORREO ENVIADO EXITOSAMENTE")
                
                return Response({
                    'status': 'sent',
                    'email_id': email.id,
                    'message': 'Correo enviado exitosamente'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                # Capturar error específico de envío
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error("="*50)
                logger.error("❌ ERROR ENVIANDO CORREO")
                logger.error(f"Mensaje de error: {error_msg}")
                logger.error(f"Traceback completo:\n{error_trace}")
                logger.error("="*50)
                
                # Verificar tipos de errores comunes
                if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    error_msg = "Error de autenticación con Resend. Verifica tu API Key en settings.py"
                elif "verified" in error_msg.lower():
                    error_msg = f"El email '{from_email}' no está verificado en Resend. Debes verificar tu dominio o email en el dashboard de Resend."
                elif "domain" in error_msg.lower():
                    error_msg = f"El dominio de '{from_email}' no está verificado en Resend."
                elif "recipient" in error_msg.lower():
                    error_msg = f"Error con los destinatarios: {error_msg}"
                
                return Response({
                    'status': 'error',
                    'message': f'Error al enviar: {error_msg}',
                    'detail': str(e),
                    'traceback': error_trace if settings.DEBUG else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error("="*50)
            logger.error("❌ ERROR GENERAL EN EL MÉTODO SEND")
            logger.error(f"Mensaje de error: {str(e)}")
            logger.error(f"Traceback completo:\n{error_trace}")
            logger.error("="*50)
            
            return Response({
                'status': 'error',
                'message': str(e),
                'traceback': error_trace if settings.DEBUG else None
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def save_draft(self, request):
        """Guardar un borrador"""
        try:
            data = request.data
            email = Email.objects.create(
                user=request.user,
                subject=data.get('subject', ''),
                sender=request.user.email or settings.DEFAULT_FROM_EMAIL,
                recipients=data.get('recipients', []),
                cc=data.get('cc', []),
                bcc=data.get('bcc', []),
                body_text=data.get('body_text', ''),
                body_html=data.get('body_html', ''),
                is_draft=True
            )
            serializer = self.get_serializer(email)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error guardando borrador: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailLabelViewSet(viewsets.ModelViewSet):
    """API para gestionar etiquetas de correos"""
    serializer_class = EmailLabelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar etiquetas del usuario autenticado"""
        return EmailLabel.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Crear una nueva etiqueta"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_emails(self, request, pk=None):
        """Añadir correos a una etiqueta"""
        label = self.get_object()
        email_ids = request.data.get('email_ids', [])
        
        if not email_ids:
            return Response({
                'status': 'error',
                'message': 'Debes especificar al menos un correo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        emails = Email.objects.filter(
            id__in=email_ids,
            user=request.user
        )
        
        label.emails.add(*emails)
        label.save()
        
        return Response({
            'status': 'success',
            'message': f'{len(emails)} correos añadidos a la etiqueta {label.name}'
        })
    
    @action(detail=True, methods=['post'])
    def remove_emails(self, request, pk=None):
        """Eliminar correos de una etiqueta"""
        label = self.get_object()
        email_ids = request.data.get('email_ids', [])
        
        if not email_ids:
            return Response({
                'status': 'error',
                'message': 'Debes especificar al menos un correo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        emails = Email.objects.filter(
            id__in=email_ids,
            user=request.user
        )
        
        label.emails.remove(*emails)
        label.save()
        
        return Response({
            'status': 'success',
            'message': f'{len(emails)} correos eliminados de la etiqueta {label.name}'
        })


# Señal para procesar correos entrantes
@receiver(inbound)
def procesar_correo_entrante(sender, event, esp_name, **kwargs):
    """Procesar correos entrantes desde Resend"""
    try:
        # Extraer datos del correo
        sender_email = event.from_email
        recipients = [to.email for to in event.to] if hasattr(event, 'to') else []
        
        # Determinar a qué usuario pertenece
        user = None
        
        # Primero intentar con el destinatario principal
        if recipients:
            try:
                user = User.objects.get(email=recipients[0])
            except User.DoesNotExist:
                # Buscar en todos los destinatarios
                for recipient in recipients:
                    try:
                        user = User.objects.get(email=recipient)
                        break
                    except User.DoesNotExist:
                        continue
        
        if not user:
            logger.warning(f"No se encontró usuario para: {recipients}")
            return
        
        # Crear el correo en la base de datos
        email = Email.objects.create(
            user=user,
            subject=event.subject or '',
            sender=sender_email,
            recipients=recipients,
            cc=[cc.email for cc in event.cc] if hasattr(event, 'cc') and event.cc else [],
            body_text=event.text or '',
            body_html=event.html or '',
            is_sent=False,
            message_id=event.message_id or '',
        )
        
        logger.info(f"Correo entrante guardado: {email.id} - {email.subject}")
        
    except Exception as e:
        logger.error(f"Error procesando correo entrante: {str(e)}")