from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                blank=True,
                choices=[("buyer", "Buyer"), ("seller", "Seller")],
                default="",
                max_length=16,
            ),
        ),
    ]
