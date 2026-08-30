from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.listings.models import Order
from modules.orders.models import OrderHistory


@receiver(post_save, sender=Order)
def log_created_order(sender, instance, created, **kwargs):
    if not created:
        return
    OrderHistory.objects.create(
        order=instance,
        status=instance.status,
        note="created",
    )
