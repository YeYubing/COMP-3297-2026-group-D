from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
import uuid


# ==================== Product Model (Sprint 2) ====================
class Product(models.Model):
    product_id = models.CharField(max_length=50, verbose_name="Product ID")  
    version = models.CharField(max_length=20, verbose_name="Version")

    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_products',
        verbose_name="Product Owner"
    )
    developers = models.ManyToManyField(User, related_name='developed_products', blank=True)
    
    description = models.TextField(blank=True, verbose_name="Product Description")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_id} (v{self.version})"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = ['product_id', 'version']   

        
# ==================== Defect Model ====================
class Defect(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='defects',
        verbose_name="Product"
    )

    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    steps_to_reproduce = models.TextField(blank=True, verbose_name="Steps to Reproduce")
    tester_id = models.CharField(max_length=100, verbose_name="Tester ID")
    tester_email = models.TextField(blank=True, help_text="Multiple mailboxes are separated by commas")

    version = models.CharField(max_length=20, verbose_name="Version")

    SEVERITY_CHOICES = [
        ('low', 'Low'), ('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name="Severity")

    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'),('critical', 'Critical')]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")

    STATUS_CHOICES = [
        ('new', 'New'), ('open', 'Open'),('rejected', 'Rejected'), ('assigned', 'Assigned'),
        ('fixed', 'Fixed'),('reopened', 'Reopened'), ('resolved', 'Resolved'),  ('duplicate', 'Duplicate'), ('cannot_reproduce', 'Canot_Reproduce'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Status")

    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Assigned To"
    )

    date_reported = models.DateTimeField(auto_now_add=True, verbose_name="Received")
    date_fixed = models.DateTimeField(null=True, blank=True, verbose_name="Fixed Date")

    def __str__(self):
        return f"#{self.id} - {self.title}"

    class Meta:
        verbose_name = "Defect"
        verbose_name_plural = "Defects"


# ==================== Email Notification ====================
@receiver(post_save, sender=Defect)
def send_defect_notification(sender, instance, created, **kwargs):

    if not instance.tester_email:
        return
    recipients = [email.strip() for email in instance.tester_email.split(',') if email.strip()]
    if not recipients:
        return

    if created:
        subject = f"BetaTrax - Defect #{instance.id} created"
        message = f"""
Defect Title: {instance.title}
Product: {instance.product.product_id} (v{instance.product.version})
Description: {instance.description}
Status: {instance.get_status_display()}
        """
    else:

        try:
            old_instance = Defect.objects.get(pk=instance.pk)
            old_status = old_instance.status
        except Defect.DoesNotExist:
            return
        if old_status == instance.status:
            return  
        subject = f"BetaTrax - Defect #{instance.id} status changed from {old_status} to {instance.get_status_display()}"
        message = f"""
Defect Title: {instance.title}
Product: {instance.product.product_id} (v{instance.product.version})
Description: {instance.description}
New Status: {instance.get_status_display()}
        """

    send_mail(
        subject=subject,
        message=message,
        from_email='betatrax@example.com',
        recipient_list=recipients,
        fail_silently=False,
    )
# ==================== comment function ====================
class Comment(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.defect.id}"
    

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