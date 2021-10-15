# Generated by Django 3.2 on 2021-10-15 14:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0058_delete_orderrestaurant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан'),
        ),
    ]
