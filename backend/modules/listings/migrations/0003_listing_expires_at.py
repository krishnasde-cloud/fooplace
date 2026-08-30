from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def default_expires_at():
    return timezone.now() + timedelta(hours=24)


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0002_buyer_order_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="expires_at",
            field=models.DateTimeField(default=default_expires_at),
        ),
    ]
