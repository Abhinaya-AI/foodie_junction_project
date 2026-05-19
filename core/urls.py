from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('',                          views.index,              name='index'),
    path('login/',                    views.login_view,         name='login'),
    path('verify-otp/',               views.otp_verify_view,    name='otp_verify'),
    path('logout/',                   views.logout_view,        name='logout'),
    path('restaurant/<int:pk>/',      views.restaurant_detail,  name='restaurant_detail'),
    path('cart/',                     views.cart_view,          name='cart'),
    path('checkout/',                 views.checkout_view,      name='checkout'),
    path('order-success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('profile/',                  views.profile_view,       name='profile'),
    path('search/',                   views.search_view,        name='search'),

    # API
    path('api/send-otp/',             views.api_send_otp,       name='api_send_otp'),
    path('api/verify-otp/',           views.api_verify_otp,     name='api_verify_otp'),
    path('api/resend-otp/',           views.api_resend_otp,     name='api_resend_otp'),
    path('api/cart/update/',          views.api_cart_update,    name='api_cart_update'),
    path('api/cart/',                 views.api_cart_details,   name='api_cart_details'),
    path('api/place-order/',          views.api_place_order,    name='api_place_order'),
    path('api/payment/verify/',       views.api_payment_verify, name='api_payment_verify'),
    path('api/restaurants/',          views.api_restaurants,    name='api_restaurants'),
    path('api/search/',               views.api_search,         name='api_search'),
    path('api/reviews/',              views.api_submit_review,  name='api_submit_review'),
    path('api/book-table/',           views.api_book_table,     name='api_book_table'),
    path('api/profile/update/',       views.api_update_profile, name='api_update_profile'),
]