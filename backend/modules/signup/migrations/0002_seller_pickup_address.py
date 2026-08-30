from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("signup", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sellerprofile",
            name="pickup_address",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="sellerprofile",
            name="pickup_lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sellerprofile",
            name="pickup_lon",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
