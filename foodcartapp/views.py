import os

import requests
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from places.models import Place

from .models import (Order, OrderItem, OrderRestaurant, Product,
                     RestaurantMenuItem)


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
    

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber' , 'address', 'products']


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


def find_restaurants(order):
    rests_for_products = []
    for order_item in OrderItem.objects.filter(customer=order):
        rests_for_product = [item.restaurant for item in 
            RestaurantMenuItem.objects.filter(product=order_item.product) if item.availability]
        rests_for_products.append(rests_for_product)
    while len(rests_for_products) != 1:
        intersection = set(rests_for_products[-1]) & set(rests_for_products[-2])
        rests_for_products.pop(-1)
        rests_for_products.pop(-1)
        rests_for_products.append(intersection)
    return list(rests_for_products[0])


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    load_dotenv()
    apikey = os.environ['YANDEX_GEO_API']

    order = request.data
    serializer = OrderSerializer(data=order)
    serializer.is_valid(raise_exception=True)
    
    customer = Order.objects.create(
        firstname = serializer.validated_data['firstname'],
        lastname = serializer.validated_data['lastname'],
        phonenumber = serializer.validated_data['phonenumber'],
        address = serializer.validated_data['address']
    )

    order_lon, order_lat = fetch_coordinates(
        apikey, serializer.validated_data['address']
    )
    obj, created = Place.objects.update_or_create(
        address = serializer.validated_data['address'],
        defaults={
            'lng': order_lon,
            'lat': order_lat
        }
    )

    for product in serializer.validated_data['products']:
        OrderItem.objects.create(
            customer = customer,
            product = product['product'],
            quantity = product['quantity'],
            price = product['product'].price
        )

    for restaurant in find_restaurants(customer):
        rest = OrderRestaurant.objects.create(
            order = customer,
            restaurant = restaurant
        )
        rest_lon, rest_lat = fetch_coordinates(
            apikey, rest.restaurant.address
        )
        obj, created = Place.objects.update_or_create(
            address = rest.restaurant.address,
            defaults={
                'lng': rest_lon,
                'lat': rest_lat
            }
        )

    serializer = OrderSerializer(customer)
    return Response(serializer.data)
