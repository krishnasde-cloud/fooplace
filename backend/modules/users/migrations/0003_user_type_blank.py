from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_type_admin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("buyer", "Buyer"),
                    ("seller", "Seller"),
                    ("admin", "Admin"),
                ],
                default="",
                max_length=16,
            ),
        ),
    ]
