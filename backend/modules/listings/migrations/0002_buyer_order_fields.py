from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="cuisine",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="order",
            name="deposit_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="order",
            name="deposit_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="deposit_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("confirmed", "Confirmed"),
                    ("ready_for_pickup", "Ready for pickup"),
                    ("completed", "Completed"),
                    ("expired", "Expired"),
                    ("picked_up", "Picked up"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
    ]
