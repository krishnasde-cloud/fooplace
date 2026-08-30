import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0003_user_type_blank"),
    ]

    operations = [
        migrations.CreateModel(
            name="Listing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dish_name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("cuisine", models.CharField(max_length=64)),
                ("neighbourhood", models.CharField(max_length=128)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("quantity_available", models.PositiveIntegerField(default=1)),
                ("photos", models.JSONField(default=list)),
                ("pickup_start", models.DateTimeField()),
                ("pickup_end", models.DateTimeField()),
                ("sold_out", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "seller",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listings",
                        to="users.user",
                    ),
                ),
            ],
        ),
    ]
