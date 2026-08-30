from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("signup", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sellerprofile",
            name="neighbourhood",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
