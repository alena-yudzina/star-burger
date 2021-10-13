from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, F, Sum
from django.db.models.deletion import SET_NULL
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_total_price(self):
            return self.annotate(
                total_price=Sum(
                    F('products__price') * F('products__quantity'),
                    output_field=DecimalField(max_digits=8, decimal_places=2)
                )
            )


class Order(models.Model):

    PROCESSED = 'processed'
    NOT_PROCESSED = 'not_processed'

    order_statuses = [
        (PROCESSED, 'Обработаный'),
        (NOT_PROCESSED, 'Необработанный')
    ]

    CASH = 'cash'
    CARD = 'card'
    NOT_SELECTED = 'not_selected'

    payment_methods = [
        (CASH, 'Наличными'),
        (CARD, 'Картой'),
        (NOT_SELECTED, 'Не выбран')
    ]

    id = models.BigAutoField(primary_key=True)
    firstname = models.CharField(
        verbose_name='Имя',
        max_length=50
    )
    lastname = models.CharField(
        verbose_name='Фамилия',
        max_length=50,
        blank=True
    )
    phonenumber = PhoneNumberField(
        verbose_name='Телефон',
        db_index=True
    )
    address = models.CharField(
        'Адрес',
        max_length=100,
    ) 
    status = models.CharField(
        verbose_name='Статус',
        max_length=13,
        choices=order_statuses,
        default=NOT_PROCESSED,
        db_index=True
    )
    payment = models.CharField(
        verbose_name='Оплата',
        max_length=13,
        choices=payment_methods,
        default=NOT_SELECTED,
        db_index=True
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='Время создания заказа',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        verbose_name='Время подтверждения заказа',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='Время доставки заказа',
        null=True,
        blank=True,
        db_index=True
    )
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Ресторан',
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class OrderItem(models.Model):
    customer = models.ForeignKey(
        Order,
        related_name='products',
        verbose_name="Покупатель",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orderes',
        verbose_name='Товар',
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Количество',
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return self.product.name


class OrderRestaurant(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='restaurants',
        verbose_name="Заказ",
        on_delete=models.CASCADE,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='order',
        verbose_name='Ресторан',
    )

    class Meta:
        verbose_name = 'Ресторан доставки'
        verbose_name_plural = 'Рестораны доставки'
    
    def __str__(self):
        return self.restaurant.name
