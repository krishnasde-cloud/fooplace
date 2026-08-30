from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_type_blank"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="user",
            name="phone",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
