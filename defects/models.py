from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_save
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
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Expiry Date")
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

    duplicate_of = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='duplicate_children'
    )

    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    steps_to_reproduce = models.TextField(blank=True, verbose_name="Steps to Reproduce")
    tester_id = models.CharField(max_length=100, verbose_name="Tester ID")
    tester_email = models.TextField(blank=True, help_text="Multiple mailboxes are separated by commas")

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


def _split_emails(value):
    return {email.strip() for email in value.split(',') if email.strip()}


def _get_duplicate_root(defect):
    current = defect
    seen = set()

    while current.duplicate_of_id is not None:
        if current.pk in seen:
            break
        seen.add(current.pk)
        current = current.duplicate_of

    return current


def _collect_duplicate_chain(defect):
    root = _get_duplicate_root(defect)
    chain = []
    seen = set()

    def visit(node):
        if node.pk in seen:
            return
        seen.add(node.pk)
        chain.append(node)
        for child in node.duplicate_children.all():
            visit(child)

    visit(root)
    return chain


def _collect_duplicate_recipients(defect):
    recipients = set()
    for linked_defect in _collect_duplicate_chain(defect):
        recipients.update(_split_emails(linked_defect.tester_email))
    return sorted(recipients)


#Notifications
@receiver(pre_save,sender=Defect)
def capture_old_status(sender,instance,**kwargs):
    if instance.pk:
        try:
            old_instance=Defect.objects.get(pk=instance.pk)
            instance._old_status=old_instance.status
        except Defect.DoesNotExist:
            instance._old_status=None
    else:
        instance._old_status=None
@receiver(post_save,sender=Defect)
def send_status_change_notification(sender,instance,created,**kwargs):
    # send an email notification when a status of existing defect changes.
    if created:
        return
    if hasattr(instance, '_old_status') and instance._old_status is not None:
        if instance._old_status !=instance.status:
            recipients = _collect_duplicate_recipients(instance)
            if recipients:
                old_status_display=dict(Defect.STATUS_CHOICES).get(instance._old_status,instance._old_status)
                new_status_display=instance.get_status_display()
                subject = f"BetaTrax - Defect #{instance.id} status changed from {old_status_display} to {new_status_display}"
                message = f"""
Defect ID: #{instance.id}
Title: {instance.title}
Product: {instance.product.product_id} (v{instance.product.version})
Description: {instance.description}

Status Update:
  From: {old_status_display}
  To:   {new_status_display}
                """
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email='kayidax@gmail.com',
                        recipient_list=recipients,
                        fail_silently=False
                    )
                except Exception as e:
                    print(f"Failed to send status notification to email: {e}")

# # ==================== Email Notification ====================
# @receiver(post_save, sender=Defect)
# def send_defect_notification(sender, instance, created, **kwargs):

#     if not instance.tester_email:
#         return
#     recipients = [email.strip() for email in instance.tester_email.split(',') if email.strip()]
#     if not recipients:
#         return

#     if created:
#         subject = f"BetaTrax - Defect #{instance.id} created"
#         message = f"""
# Defect Title: {instance.title}
# Product: {instance.product.product_id} (v{instance.product.version})
# Description: {instance.description}
# Status: {instance.get_status_display()}
#         """
#     else:

#         try:
#             old_instance = Defect.objects.get(pk=instance.pk)
#             old_status = old_instance.status
#         except Defect.DoesNotExist:
#             return
#         if old_status == instance.status:
#             return  
#         subject = f"BetaTrax - Defect #{instance.id} status changed from {old_status} to {instance.get_status_display()}"
#         message = f"""
# Defect Title: {instance.title}
# Product: {instance.product.product_id} (v{instance.product.version})
# Description: {instance.description}
# New Status: {instance.get_status_display()}
#         """

#     send_mail(
#         subject=subject,
#         message=message,
#         from_email='betatrax@example.com',
#         recipient_list=recipients,
#         fail_silently=False,
#     )
# ==================== comment function ====================
class Comment(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.defect.id}"
    




# ==================== Defect History ====================
class DefectHistory(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='defect_history_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='defect_history_assigned')
