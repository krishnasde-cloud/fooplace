from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("confirmed", "Confirmed"),
                    ("picked_up", "Picked up"),
                    ("cancelled", "Cancelled"),
                    ("expired", "Expired"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
    ]
