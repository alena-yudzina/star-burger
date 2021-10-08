from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True
    )
    lng = models.DecimalField(
        max_digits=16,
        decimal_places=14,
        verbose_name='Долгота'
        )
    lat = models.DecimalField(
        max_digits=16,
        decimal_places=14,
        verbose_name='Широта'
        )
    created_at = models.DateTimeField(
        verbose_name='Дата получения координат',
        default=timezone.now
    )
