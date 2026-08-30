from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from modules.backoffice.models import SellerReview
from modules.signup.models import SellerProfile


@receiver(post_save, sender=SellerProfile)
def queue_seller_review(sender, instance, created, **kwargs):
    if created:
        SellerReview.objects.get_or_create(user=instance.user)


@receiver(post_delete, sender=SellerProfile)
def drop_seller_review(sender, instance, **kwargs):
    SellerReview.objects.filter(user=instance.user).delete()
