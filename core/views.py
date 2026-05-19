import json, razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q, Avg
from django.utils import timezone
from decimal import Decimal
from .models import User, OTP, Restaurant, FoodItem, Cart, CartItem, Order, OrderItem, Review, TableBooking
from .utils import send_otp_email, send_order_confirmation_email


# ── Page Views ───────────────────────────────────
def index(request):
    city = request.GET.get('city', 'bangalore')
    qs   = Restaurant.objects.filter(city=city, is_open=True)
    if request.GET.get('rating') == '4plus': qs = qs.filter(rating__gte=4.0)
    if request.GET.get('pure_veg') == '1':   qs = qs.filter(is_pure_veg=True)
    if request.GET.get('serves_alcohol')=='1': qs = qs.filter(serves_alcohol=True)
    search = request.GET.get('search', '')
    if search: qs = qs.filter(Q(name__icontains=search)|Q(cuisine_types__icontains=search))
    sort = request.GET.get('sort', 'relevance')
    sort_map = {
        'rating': '-rating',
        'delivery': 'delivery_time_min',
        'cost_low': 'avg_cost_for_two',
        'cost_high': '-avg_cost_for_two',
    }

    if sort in sort_map:
        qs = qs.order_by(sort_map[sort])
    else:
        qs = qs.order_by('-is_featured', '-rating')

    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart_count = Cart.objects.get(user=request.user).item_count
        except:
            pass
    return render(request, 'index.html', {
        'restaurants': qs, 'selected_city': city,
        'cities': ['bangalore','delhi','hyderabad','mumbai','kolkata'],
        'search_query': search, 'sort_by': sort, 'cart_count': cart_count,
        'categories': [
            {'slug':'biryani','name':'Biryani','emoji':'🍛','color':'#FF6B35'},
            {'slug':'south_indian','name':'South Indian','emoji':'🫓','color':'#F7931E'},
            {'slug':'rolls','name':'Rolls','emoji':'🌯','color':'#4CAF50'},
            {'slug':'shakes','name':'Shakes','emoji':'🥤','color':'#9C27B0'},
            {'slug':'pizza','name':'Pizza','emoji':'🍕','color':'#E91E63'},
            {'slug':'burgers','name':'Burgers','emoji':'🍔','color':'#FF5722'},
        ],
    })

def login_view(request):
    if request.user.is_authenticated: return redirect('index')
    return render(request, 'login.html')

def otp_verify_view(request):
    email = request.session.get('otp_email')
    if not email: return redirect('login')
    return render(request, 'otp_verify.html', {'email': email})

def logout_view(request):
    logout(request)
    return redirect('login')

def restaurant_detail(request, pk):
    r       = get_object_or_404(Restaurant, pk=pk)
    items   = r.food_items.filter(is_available=True)
    reviews = r.reviews.filter(is_approved=True)[:10]
    cats = {}
    for item in items:
        cat = item.get_category_display()
        cats.setdefault(cat, []).append(item)
    cart_items, cart_count = {}, 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.item_count
            for ci in cart.items.all(): cart_items[ci.food_item_id] = ci.quantity
        except: pass
    return render(request, 'restaurant_detail.html', {
        'restaurant': r, 'categories': cats, 'reviews': reviews,
        'cart_items': json.dumps(cart_items), 'cart_count': cart_count,
    })

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    subtotal = cart.total
    delivery_fee = Decimal('40') if subtotal > 0 else Decimal('0')
    return render(request, 'cart.html', {
        'cart': cart, 'items': cart.items.all(),
        'subtotal': subtotal, 'delivery_fee': delivery_fee,
        'total': subtotal + delivery_fee, 'cart_count': cart.item_count,
    })

@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists(): return redirect('cart')
    subtotal = cart.total
    delivery_fee = Decimal('40')
    return render(request, 'checkout.html', {
        'cart': cart, 'items': cart.items.all(),
        'subtotal': subtotal, 'delivery_fee': delivery_fee,
        'total': subtotal + delivery_fee,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'cart_count': cart.item_count, 'user': request.user,
    })

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order, 'cart_count': 0})

@login_required
def profile_view(request):
    orders   = Order.objects.filter(user=request.user).prefetch_related('items__food_item')[:10]
    bookings = TableBooking.objects.filter(user=request.user)[:5]
    cart_count = 0
    try: cart_count = Cart.objects.get(user=request.user).item_count
    except: pass
    return render(request, 'profile.html', {'orders': orders, 'bookings': bookings, 'cart_count': cart_count})

def search_view(request):
    q       = request.GET.get('q', '')
    results = {'restaurants': [], 'food_items': []}
    if q:
        results['restaurants'] = Restaurant.objects.filter(Q(name__icontains=q)|Q(cuisine_types__icontains=q))[:10]
        results['food_items']  = FoodItem.objects.filter(Q(name__icontains=q)).select_related('restaurant')[:10]
    cart_count = 0
    if request.user.is_authenticated:
        try: cart_count = Cart.objects.get(user=request.user).item_count
        except: pass
    return render(request, 'search.html', {'query': q, 'results': results, 'cart_count': cart_count})


# ── API Views ────────────────────────────────────
@require_http_methods(["POST"])
def api_send_otp(request):
    try:
        data  = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        if not email or '@' not in email:
            return JsonResponse({'success': False, 'message': 'Enter a valid email.'})
        otp = OTP.generate_otp(email)
        user_name = ''
        try: user_name = User.objects.get(email=email).get_full_name()
        except: pass
        send_otp_email(email, otp.otp_code, user_name)
        request.session['otp_email'] = email
        return JsonResponse({'success': True, 'message': f'OTP sent to {email}', 'redirect': '/verify-otp/'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_http_methods(["POST"])
def api_verify_otp(request):
    try:
        data     = json.loads(request.body)
        email    = request.session.get('otp_email', '').lower()
        otp_code = data.get('otp', '').strip()
        if not email:
            return JsonResponse({'success': False, 'message': 'Session expired.'})
        if len(otp_code) != 6:
            return JsonResponse({'success': False, 'message': 'Enter a valid 6-digit OTP.'})
        try:
            otp = OTP.objects.filter(email=email, otp_code=otp_code, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid OTP.'})
        if not otp.is_valid():
            return JsonResponse({'success': False, 'message': 'OTP expired. Request a new one.'})
        otp.is_used = True
        otp.save()
        user, created = User.objects.get_or_create(email=email)
        user.backend  = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session.pop('otp_email', None)
        return JsonResponse({'success': True, 'is_new_user': created, 'redirect': '/'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_http_methods(["POST"])
def api_resend_otp(request):
    email = request.session.get('otp_email', '')
    if not email: return JsonResponse({'success': False, 'message': 'Session expired.'})
    otp = OTP.generate_otp(email)
    send_otp_email(email, otp.otp_code)
    return JsonResponse({'success': True, 'message': 'New OTP sent!'})


@login_required
@require_http_methods(["POST"])
def api_cart_update(request):
    try:
        data         = json.loads(request.body)
        food_item    = get_object_or_404(FoodItem, id=data.get('food_item_id'))
        action       = data.get('action', 'add')
        cart, _      = Cart.objects.get_or_create(user=request.user)
        if cart.restaurant and cart.restaurant != food_item.restaurant and action == 'add':
            return JsonResponse({'success': False, 'different_restaurant': True,
                'message': f'Cart has items from {cart.restaurant.name}. Clear to add from {food_item.restaurant.name}?'})
        if action == 'add':
            cart.restaurant = food_item.restaurant; cart.save()
            ci, created = CartItem.objects.get_or_create(cart=cart, food_item=food_item)
            if not created: ci.quantity += 1; ci.save()
        elif action == 'remove':
            try:
                ci = CartItem.objects.get(cart=cart, food_item=food_item)
                if ci.quantity > 1: ci.quantity -= 1; ci.save()
                else: ci.delete()
            except CartItem.DoesNotExist: pass
        elif action in ('delete','clear'):
            if action == 'clear': cart.items.all().delete(); cart.restaurant = None; cart.save()
            else: CartItem.objects.filter(cart=cart, food_item=food_item).delete()
        try: qty = CartItem.objects.get(cart=cart, food_item=food_item).quantity
        except: qty = 0
        if cart.item_count == 0: cart.restaurant = None; cart.save()
        return JsonResponse({'success': True, 'cart_count': cart.item_count,
                             'item_quantity': qty, 'cart_total': float(cart.total)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def api_cart_details(request):
    try:
        cart  = Cart.objects.get(user=request.user)
        items = [{'id': ci.id, 'food_item_id': ci.food_item_id, 'name': ci.food_item.name,
                  'price': float(ci.food_item.price), 'quantity': ci.quantity,
                  'subtotal': float(ci.subtotal)} for ci in cart.items.select_related('food_item').all()]
        return JsonResponse({'success': True, 'items': items, 'total': float(cart.total), 'item_count': cart.item_count})
    except Cart.DoesNotExist:
        return JsonResponse({'success': True, 'items': [], 'total': 0, 'item_count': 0})


@login_required
@require_http_methods(["POST"])
def api_place_order(request):
    try:
        data = json.loads(request.body)
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists(): return JsonResponse({'success': False, 'message': 'Cart is empty.'})
        subtotal     = cart.total
        delivery_fee = Decimal('40')
        total        = subtotal + delivery_fee
        order = Order.objects.create(
            user=request.user, restaurant=cart.restaurant,
            delivery_name=data['name'], delivery_phone=data['phone'],
            delivery_address=data['address'], delivery_pincode=data['pincode'],
            payment_method=data['payment_method'], payment_status='pending',
            subtotal=subtotal, delivery_fee=delivery_fee, total_amount=total,
            special_instructions=data.get('instructions',''),
        )
        for ci in cart.items.all():
            OrderItem.objects.create(order=order, food_item=ci.food_item,
                                     quantity=ci.quantity, unit_price=ci.food_item.price)
        if data['payment_method'] == 'online':
            try:
                client   = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                rz_order = client.order.create({'amount': int(total*100), 'currency': 'INR', 'receipt': f'order_{order.id}'})
                order.razorpay_order_id = rz_order['id']; order.save()
                cart.items.all().delete(); cart.restaurant = None; cart.save()
                return JsonResponse({'success': True, 'payment_required': True,
                    'razorpay_order_id': rz_order['id'], 'amount': int(total*100), 'order_id': order.id})
            except Exception as e:
                order.delete()
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            order.status = 'confirmed'; order.save()
            send_order_confirmation_email(order)
            cart.items.all().delete(); cart.restaurant = None; cart.save()
            return JsonResponse({'success': True, 'payment_required': False,
                                 'order_id': order.id, 'redirect': f'/order-success/{order.id}/'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def api_payment_verify(request):
    try:
        data   = json.loads(request.body)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            'razorpay_order_id':   data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature':  data['razorpay_signature'],
        })
        order = Order.objects.get(razorpay_order_id=data['razorpay_order_id'])
        order.razorpay_payment_id = data['razorpay_payment_id']
        order.payment_status = 'paid'; order.status = 'confirmed'; order.save()
        send_order_confirmation_email(order)
        return JsonResponse({'success': True, 'redirect': f'/order-success/{order.id}/'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def api_restaurants(request):
    city, search = request.GET.get('city','bangalore'), request.GET.get('search','')
    qs = Restaurant.objects.filter(is_open=True, city=city)
    if search: qs = qs.filter(Q(name__icontains=search)|Q(cuisine_types__icontains=search))
    data = [{'id':r.id,'name':r.name,'city':r.city,'rating':float(r.rating),
             'distance_km':float(r.distance_km),'is_pure_veg':r.is_pure_veg,
             'serves_alcohol':r.serves_alcohol,'image':r.get_image(),
             'cuisine_types':r.cuisine_list,'avg_cost_for_two':r.avg_cost_for_two,
             'delivery_time_min':r.delivery_time_min} for r in qs[:20]]
    return JsonResponse({'success': True, 'restaurants': data})


def api_search(request):
    q = request.GET.get('q', '')
    if len(q) < 2: return JsonResponse({'restaurants': [], 'food_items': []})
    restaurants = Restaurant.objects.filter(Q(name__icontains=q)|Q(cuisine_types__icontains=q))[:5]
    food_items  = FoodItem.objects.filter(Q(name__icontains=q)).select_related('restaurant')[:5]
    return JsonResponse({
        'restaurants': [{'id':r.id,'name':r.name,'city':r.city,'rating':float(r.rating)} for r in restaurants],
        'food_items':  [{'id':f.id,'name':f.name,'restaurant':f.restaurant.name,
                         'restaurant_id':f.restaurant_id,'price':float(f.price)} for f in food_items],
    })


@login_required
@require_http_methods(["POST"])
def api_submit_review(request):
    try:
        data       = json.loads(request.body)
        restaurant = get_object_or_404(Restaurant, id=data['restaurant_id'])
        review, _  = Review.objects.update_or_create(
            user=request.user, restaurant=restaurant,
            defaults={'rating':data.get('rating',4),'comment':data.get('comment',''),
                      'food_rating':data.get('food_rating',4),'delivery_rating':data.get('delivery_rating',4)}
        )
        avg = restaurant.reviews.aggregate(avg=Avg('rating'))['avg']
        if avg: restaurant.rating = round(avg,1); restaurant.num_ratings = restaurant.reviews.count(); restaurant.save()
        return JsonResponse({'success': True, 'message': 'Review submitted!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def api_book_table(request):
    try:
        data    = json.loads(request.body)
        r       = get_object_or_404(Restaurant, id=data['restaurant_id'])
        booking = TableBooking.objects.create(
            user=request.user, restaurant=r,
            booking_date=data['date'], booking_time=data['time'],
            num_guests=data.get('guests',2), name=data['name'],
            phone=data['phone'], email=request.user.email,
            special_requests=data.get('special_requests',''),
        )
        return JsonResponse({'success': True, 'message': f'Table booked for {booking.num_guests} guests!', 'booking_id': booking.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def api_update_profile(request):
    try:
        data = json.loads(request.body)
        request.user.name  = data.get('name', request.user.name)
        request.user.phone = data.get('phone', request.user.phone)
        request.user.save()
        return JsonResponse({'success': True, 'message': 'Profile updated!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})