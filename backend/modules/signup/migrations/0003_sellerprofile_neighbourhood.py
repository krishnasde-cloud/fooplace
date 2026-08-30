from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("signup", "0002_seller_pickup_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="sellerprofile",
            name="neighbourhood",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
