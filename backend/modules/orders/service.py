from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from modules.listings.models import Listing, Order
from modules.orders.models import BuyerNotification, OrderHistory


def confirm_hours() -> int:
    return int(getattr(settings, "ORDER_CONFIRM_HOURS", 4))


def is_overdue(order: Order, now=None) -> bool:
    now = now or timezone.now()
    return order.created_at <= now - timedelta(hours=confirm_hours())


def record_status(order: Order, status: str, *, note: str = "") -> OrderHistory:
    if order.status != status:
        order.status = status
        order.save(update_fields=["status", "updated_at"])
    return OrderHistory.objects.create(order=order, status=status, note=note)


def notify_buyer(order: Order, kind: str, message: str) -> BuyerNotification:
    notice = BuyerNotification.objects.create(
        buyer=order.buyer,
        order=order,
        kind=kind,
        message=message,
    )
    email = order.buyer.email
    if email:
        send_mail(
            "Fooplace order update",
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", "fooplace@localhost"),
            [email],
            fail_silently=True,
        )
    return notice


@transaction.atomic
def expire_order(order: Order) -> Order:
    order = (
        Order.objects.select_for_update()
        .select_related("listing", "buyer")
        .get(pk=order.pk)
    )
    if order.status != Order.Status.PENDING:
        return order

    listing = Listing.objects.select_for_update().get(pk=order.listing_id)
    listing.quantity_available += order.quantity
    if listing.status == Listing.Status.SOLD_OUT and listing.quantity_available > 0:
        listing.status = Listing.Status.ACTIVE
    listing.save(update_fields=["quantity_available", "status", "updated_at"])
    record_status(
        order,
        Order.Status.EXPIRED,
        note="seller did not confirm in time",
    )
    notify_buyer(
        order,
        BuyerNotification.Kind.EXPIRED,
        (
            f"Your order for {order.listing.dish_name} expired because the "
            "seller did not confirm the e-transfer in time."
        ),
    )
    return order


def expire_overdue(now=None) -> list[Order]:
    now = now or timezone.now()
    cutoff = now - timedelta(hours=confirm_hours())
    pending = list(
        Order.objects.filter(
            status=Order.Status.PENDING,
            created_at__lte=cutoff,
        ).select_related("listing", "buyer")
    )
    return [expire_order(order) for order in pending]


@transaction.atomic
def confirm_order(order: Order, *, etransfer_received) -> Order | JsonResponse:
    if etransfer_received is not True:
        return JsonResponse({"detail": "etransfer_not_checked"}, status=400)

    order = (
        Order.objects.select_for_update()
        .select_related("listing", "buyer")
        .get(pk=order.pk)
    )
    if is_overdue(order):
        expire_order(order)
        return JsonResponse({"detail": "expired"}, status=400)
    if order.status != Order.Status.PENDING:
        return JsonResponse({"detail": "invalid_status"}, status=400)

    record_status(
        order,
        Order.Status.CONFIRMED,
        note="seller confirmed after checking e-transfer inbox",
    )
    return order
