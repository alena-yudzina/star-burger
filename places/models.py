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
        blank=True,
        verbose_name='Долгота'
        )
    lat = models.DecimalField(
        max_digits=16,
        decimal_places=14,
        blank=True,
        verbose_name='Широта'
        )
    updated_at = models.DateTimeField(
        verbose_name='Дата обновления координат',
        auto_now=True
    )
