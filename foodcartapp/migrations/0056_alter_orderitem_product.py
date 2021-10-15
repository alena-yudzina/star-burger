# Generated by Django 3.2 on 2021-10-15 12:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0055_alter_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='foodcartapp.product', verbose_name='Товар'),
        ),
    ]
