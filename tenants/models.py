from django_tenants.models import TenantMixin, DomainMixin
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    auto_create_schema = True

    class Meta:
        verbose_name = 'Client (Tenant)'
        verbose_name_plural = 'Clients (Tenants)'

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass


# ==================== User ID ====================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    custom_user_id = models.CharField(max_length=20, unique=True, blank=True, editable=False)

    def __str__(self):
        return f"{self.user.username} - {self.custom_user_id}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        unique_id = uuid.uuid4().hex[:8].upper()
        UserProfile.objects.create(user=instance, custom_user_id=unique_id)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance, custom_user_id=uuid.uuid4().hex[:8].upper())

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance, custom_user_id=uuid.uuid4().hex[:8].upper())
    else:
        instance.profile.save()
