import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("listings", "0001_initial"),
        ("users", "0003_user_type_blank"),
    ]

    operations = [
        migrations.CreateModel(
            name="SellerReview",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("flagged", models.BooleanField(default=False)),
                ("removed", models.BooleanField(default=False)),
                ("note", models.CharField(blank=True, max_length=240)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seller_review",
                        to="users.user",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ListingModeration",
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
                ("flagged", models.BooleanField(default=False)),
                ("removed", models.BooleanField(default=False)),
                ("note", models.CharField(blank=True, max_length=240)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "listing",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moderation",
                        to="listings.listing",
                    ),
                ),
            ],
        ),
    ]
