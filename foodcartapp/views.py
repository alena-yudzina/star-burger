import json
import foodcartapp

import phonenumbers
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    order = request.data
    print(order)

    fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']
    for field in fields:
        try:
            order[field]
        except KeyError:
            content = {'products, firstname, lastname, phonenumber, address': 'Обязательное поле'}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)

    if isinstance(order['products'], str):
        content = {'products': 'Ожидался list со значениями, но был получен str'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)

    if isinstance(order['firstname'], list):
        content = {'firstname': 'Not a valid string'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)

    for field in fields:
        if order[field] is None or not order[field]:
            content = {field: 'Это поле не может быть пустым'}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)

    phonenumber = phonenumbers.parse(order['phonenumber'])
    if not phonenumbers.is_valid_number(phonenumber):
        content = {'phonenumber': 'Введен некорректный номер телефона'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    customer = Order.objects.create(
        name = order['firstname'],
        surname = order['lastname'],
        phone = order['phonenumber'],
        address = order['address']
    )
    for product in order['products']:
        try:
            OrderItem.objects.create(
                customer = customer,
                product = Product.objects.get(id=product['product']),
                quantity = product['quantity']
            )
        except foodcartapp.models.Product.DoesNotExist:
            customer.delete()
            content = {'products': 'Недопустимый первичный ключ {}'.format(product['product'])}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response(order)
