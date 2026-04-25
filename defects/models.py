from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django_tenants.models import DomainMixin, TenantMixin


# ==================== Product Model (Sprint 2) ====================
class Product(models.Model):
    product_id = models.CharField(max_length=50, verbose_name="Product ID")   # 移除 unique=True
    version = models.CharField(max_length=20, verbose_name="Version")
    
    # 這個 Product 屬於哪一位 Product Owner
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_products',
        verbose_name="Product Owner"
    )
    
    description = models.TextField(blank=True, verbose_name="Product Description")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_id} (v{self.version})"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = ['product_id', 'version']   # 關鍵：允許同一個 product_id 有不同 version

        
# ==================== Defect Model ====================
class Defect(models.Model):
    # 現在改成 ForeignKey 關聯到 Product（這是重點）
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='defects',
        verbose_name="Product"
    )

    # Tester 提交時提供的欄位
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    steps_to_reproduce = models.TextField(blank=True, verbose_name="Steps to Reproduce")
    tester_id = models.CharField(max_length=100, verbose_name="Tester ID")
    reporter_email = models.EmailField(verbose_name="Reporter Email")

    version = models.CharField(max_length=20, verbose_name="Version")

    # 後續才設定的欄位
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


# ==================== Tenant Model (Sprint 3 - 必须正确配置) ====================
# class Client(TenantMixin):
#     name = models.CharField(max_length=100)
#     paid_until = models.DateField(null=True, blank=True)
#     on_trial = models.BooleanField(default=True)
#     auto_create_schema = True

#     class Meta:
#         verbose_name = 'Client (Tenant)'
#         verbose_name_plural = 'Clients (Tenants)'

#     def __str__(self):
#         return self.name

# class Domain(DomainMixin):
#     pass

# ==================== Email Notification ====================
@receiver(post_save, sender=Defect)
def send_defect_notification(sender, instance, created, **kwargs):
    if created:
        action = "created"
    else:
        action = "status updated"

    subject = f"BetaTrax - Defect #{instance.id} {action} - {instance.get_status_display()}"
    message = f"""
Defect Title: {instance.title}
Current Status: {instance.get_status_display()}
Reporter Email: {instance.reporter_email}
    """

    send_mail(
        subject=subject,
        message=message,
        from_email='betatrax@example.com',
        recipient_list=[instance.reporter_email],
        fail_silently=False,
    )