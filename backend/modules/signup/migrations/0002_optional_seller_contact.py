from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("signup", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sellerprofile",
            name="etransfer_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name="sellerprofile",
            name="facebook_marketplace_url",
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
