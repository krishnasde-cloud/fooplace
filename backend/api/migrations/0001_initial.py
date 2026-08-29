from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("user_id", models.CharField(max_length=64, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("connected_using", models.CharField(blank=True, max_length=64)),
                (
                    "user_type",
                    models.CharField(
                        choices=[("buyer", "Buyer"), ("seller", "Seller")],
                        default="buyer",
                        max_length=16,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("is_verified", models.BooleanField(default=False)),
                ("first_logged_in", models.DateTimeField()),
                ("last_logged_in", models.DateTimeField()),
            ],
        ),
    ]
