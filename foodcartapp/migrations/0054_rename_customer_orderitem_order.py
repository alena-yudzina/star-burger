# Generated by Django 3.2 on 2021-10-13 10:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0053_auto_20211013_1040'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='customer',
            new_name='order',
        ),
    ]
