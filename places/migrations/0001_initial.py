# Generated by Django 3.2 on 2021-10-08 15:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(blank=True, max_length=100, verbose_name='адрес')),
                ('coordinates_lng', models.DecimalField(decimal_places=14, max_digits=16, verbose_name='Долгота')),
                ('coordinates_lat', models.DecimalField(decimal_places=14, max_digits=16, verbose_name='Широта')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата получения координат')),
            ],
        ),
    ]
