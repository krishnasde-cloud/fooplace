from django.core.management.base import BaseCommand

from modules.orders.service import expire_overdue


class Command(BaseCommand):
    help = "Expire pending orders whose seller confirmation window has passed."

    def handle(self, *args, **options):
        expired = expire_overdue()
        self.stdout.write(f"expired {len(expired)} order(s)")
