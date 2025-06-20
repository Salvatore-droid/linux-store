# Generated by Django 5.2.2 on 2025-06-11 01:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='installedapp',
            name='app_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='installedapp',
            unique_together={('user', 'app_id')},
        ),
    ]
