import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SellerProfile",
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
                ("has_food_handler_certification", models.BooleanField(default=False)),
                ("accepted_terms", models.BooleanField(default=False)),
                ("facebook_marketplace_url", models.URLField(max_length=500)),
                ("etransfer_email", models.EmailField(max_length=254)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seller_profile",
                        to="users.user",
                    ),
                ),
            ],
        ),
    ]
