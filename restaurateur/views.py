from django.db.models.expressions import OuterRef, Subquery
import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from dotenv import load_dotenv
from geopy import distance

from foodcartapp.models import Order, Product, Restaurant, RestaurantMenuItem
from places.models import Place


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, addresses):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    addresses_with_coords = []
    for address in addresses:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not found_places:
            addresses_with_coords.append(
                {
                    'address': address,
                    'lng': 0,
                    'lat': 0
                }
            )
        else:
            most_relevant = found_places[0]
            lng, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
            addresses_with_coords.append(
                {
                    'address': address,
                    'lng': lng,
                    'lat': lat
                }
            )
        return addresses_with_coords


def get_order_details(order, restaurants):

    rest_distance = []
    for rest in restaurants:
        rest_distance.append({
            'name': rest.restaurant.name,
            'distance': round(distance.distance(
                (order.lng, order.lat), (rest.lng, rest.lat)
            ).km, 2),
        })
    rest_distance = sorted(rest_distance, key=lambda k: k['distance'])
    
    return {
        'id': order.id,
        'status': order.get_status_display(),
        'total_price': order.total_price,
        'firstname': order.firstname,
        'lastname': order.lastname,
        'address': order.address,
        'phonenumber': order.phonenumber,
        'comment': order.comment,
        'payment': order.get_payment_display(),
        'restaurant': rest_distance
    }


def find_restaurants(order, rests_menu):
    
    rests_for_products = []
    for order_item in order.order_items.all():
        rests_for_product = list(filter(lambda rest: rest.product==order_item.product and rest.availability==True, rests_menu))
        rests_for_products.append(rests_for_product)
    appropriate_rests = set(rests_for_products[0])
    for rests in rests_for_products:
        appropriate_rests = appropriate_rests & set(rests)
    return appropriate_rests


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    
    places = Place.objects.all()
    orders = (
        Order.objects
        .get_total_price()
        .prefetch_related('order_items')
        .annotate(
            lng=Subquery(places.filter(address=OuterRef('address')).values('lng')),
            lat=Subquery(places.filter(address=OuterRef('address')).values('lat'))
        )
    )
    apikey = settings.YANDEX_GEO_API

    addresses = list(orders.values_list('address', flat=True))
    restaurants = (
        Restaurant.objects
        .all()
        .annotate(
            lng=Subquery(places.filter(address=OuterRef('address')).values('lng')),
            lat=Subquery(places.filter(address=OuterRef('address')).values('lat'))
        )
    )

    addresses.extend(list(restaurants.values_list('address', flat=True)))
    exist_addresses = list(Place.objects.values_list('address', flat=True))
    addresses_to_add = list(set(addresses) - set(exist_addresses))

    if addresses_to_add:
        addresses_with_coords = fetch_coordinates(apikey, addresses_to_add)
        Place.objects.bulk_create([
            Place(address=place['address'], lng=place['lng'], lat=place['lat'])
            for place in addresses_with_coords
        ])

    rests_menu = (
        RestaurantMenuItem.objects
        .select_related('restaurant')
        .select_related('product')
        .annotate(
            lng=Subquery(places.filter(address=OuterRef('restaurant__address')).values('lng')),
            lat=Subquery(places.filter(address=OuterRef('restaurant__address')).values('lat'))
        )
    )

    return render(request, template_name='order_items.html', context={
        'order_items': [
            get_order_details( 
                order, find_restaurants(order, rests_menu)
            ) for order in orders 
        ]
    })
