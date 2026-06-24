from django.db import models
import uuid
# Create your models here.


class Driver(models.Model):
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_id = models.CharField()
    license = models.CharField(max_length=255, unique=True, null=True, blank=True)
    expiration_date = models.DateField()
    rif = models.CharField(max_length=255, unique=True, null=True, blank=True)
    photo = models.TextField(blank=True, null=True)  # o usar ImageField
    medical_certificate = models.TextField(blank=True, null=True)
    driver_status = models.CharField(
        max_length=20,
    )
    working = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drivers'
        managed = False
    
    def save(self, *args, **kwargs):
        # Asegurar que guarda en BD legacy
        if not hasattr(self, '_state'):
            self._state = type('State', (), {'db': 'legacy'})()
        super().save(*args, **kwargs)