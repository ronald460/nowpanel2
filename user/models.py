from django.db import models
import uuid

# Create your models here.


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    document = models.CharField(max_length=50, blank=True, null=True)
    document_file = models.TextField(blank=True, null=True)
    profile_photo = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=20)
    birthdate = models.CharField(max_length=255, blank=True, null=True)  # timestamp como string
    points = models.IntegerField(default=0)
    deleted = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
    )
    deletion_requested_at = models.DateTimeField(blank=True, null=True)
    deletion_scheduled_at = models.DateTimeField(blank=True, null=True)
    deletion_status = models.CharField(
        max_length=20,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        managed = False
    
    def save(self, *args, **kwargs):
        # Asegurar que guarda en BD legacy
        if not hasattr(self, '_state'):
            self._state = type('State', (), {'db': 'legacy'})()
        super().save(*args, **kwargs)