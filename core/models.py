from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import random


# ── Custom User Manager ──────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, name='', **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user


# ── User Model ───────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    email      = models.EmailField(unique=True)
    name       = models.CharField(max_length=120, blank=True)
    phone      = models.CharField(max_length=15, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined= models.DateTimeField(default=timezone.now)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self): return self.email
    def get_full_name(self): return self.name or self.email.split('@')[0]


# ── OTP Model ────────────────────────────────────
class OTP(models.Model):
    email      = models.EmailField()
    otp_code   = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)

    class Meta: ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_otp(cls, email):
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        code = str(random.randint(100000, 999999))
        return cls.objects.create(
            email=email, otp_code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

    def __str__(self): return f"{self.email} - {self.otp_code}"


# ── Choices ──────────────────────────────────────
CITY_CHOICES = [
    ('bangalore','Bangalore'), ('delhi','Delhi'),
    ('hyderabad','Hyderabad'), ('mumbai','Mumbai'), ('kolkata','Kolkata'),
]
CATEGORY_CHOICES = [
    ('biryani','Biryani'), ('south_indian','South Indian'),
    ('paratha','Paratha'), ('rolls','Rolls'), ('shakes','Shakes'),
    ('pizza','Pizza'), ('burgers','Burgers'), ('chinese','Chinese'),
    ('desserts','Desserts'), ('north_indian','North Indian'),
]


# ── Restaurant ───────────────────────────────────
class Restaurant(models.Model):
    name             = models.CharField(max_length=200)
    city             = models.CharField(max_length=50, choices=CITY_CHOICES)
    address          = models.TextField()
    rating           = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    num_ratings      = models.IntegerField(default=0)
    distance_km      = models.DecimalField(max_digits=5, decimal_places=1, default=2.0)
    is_pure_veg      = models.BooleanField(default=False)
    serves_alcohol   = models.BooleanField(default=False)
    image            = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    image_url        = models.URLField(blank=True)
    cuisine_types    = models.CharField(max_length=300, blank=True)
    avg_cost_for_two = models.IntegerField(default=400)
    min_order        = models.IntegerField(default=99)
    delivery_time_min= models.IntegerField(default=30)
    is_open          = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['-rating', '-num_ratings']

    def __str__(self): return f"{self.name} ({self.city})"

    def get_image(self):
        if self.image: return self.image.url
        return self.image_url or '/static/images/restaurant_default.jpg'

    @property
    def cuisine_list(self):
        return [c.strip() for c in self.cuisine_types.split(',') if c.strip()]


# ── FoodItem ─────────────────────────────────────
class FoodItem(models.Model):
    restaurant   = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='food_items')
    name         = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image        = models.ImageField(upload_to='food_items/', blank=True, null=True)
    image_url    = models.URLField(blank=True)
    is_veg       = models.BooleanField(default=True)
    is_bestseller= models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    rating       = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['category', 'name']

    def __str__(self): return f"{self.name} - {self.restaurant.name}"

    def get_image(self):
        if self.image: return self.image.url
        return self.image_url or '/static/images/food_default.jpg'


# ── Cart ─────────────────────────────────────────
class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Cart of {self.user.email}"

    @property
    def total(self): return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self): return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart                = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    food_item           = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity            = models.PositiveIntegerField(default=1)
    special_instructions= models.CharField(max_length=300, blank=True)
    added_at            = models.DateTimeField(auto_now_add=True)

    class Meta: unique_together = ('cart', 'food_item')

    @property
    def subtotal(self): return self.food_item.price * self.quantity


# ── Order ─────────────────────────────────────────
ORDER_STATUS   = [('pending','Pending'),('confirmed','Confirmed'),('preparing','Preparing'),
                  ('out_for_delivery','Out for Delivery'),('delivered','Delivered'),('cancelled','Cancelled')]
PAYMENT_METHOD = [('cod','Cash on Delivery'),('online','Online Payment')]
PAYMENT_STATUS = [('pending','Pending'),('paid','Paid'),('failed','Failed'),('refunded','Refunded')]

class Order(models.Model):
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant         = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    status             = models.CharField(max_length=30, choices=ORDER_STATUS, default='pending')
    payment_method     = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cod')
    payment_status     = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    razorpay_order_id  = models.CharField(max_length=100, blank=True)
    razorpay_payment_id= models.CharField(max_length=100, blank=True)
    delivery_name      = models.CharField(max_length=120)
    delivery_phone     = models.CharField(max_length=15)
    delivery_address   = models.TextField()
    delivery_pincode   = models.CharField(max_length=10)
    subtotal           = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee       = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    discount           = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_amount       = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions= models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)

    class Meta: ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.estimated_delivery:
            self.estimated_delivery = timezone.now() + timedelta(minutes=45)
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order               = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item           = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity            = models.PositiveIntegerField(default=1)
    unit_price          = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions= models.CharField(max_length=300, blank=True)

    @property
    def subtotal(self): return self.unit_price * self.quantity


# ── Review ────────────────────────────────────────
class Review(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    restaurant      = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    order           = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True)
    rating          = models.IntegerField(choices=[(i,i) for i in range(1,6)])
    title           = models.CharField(max_length=200, blank=True)
    comment         = models.TextField()
    food_rating     = models.IntegerField(choices=[(i,i) for i in range(1,6)], default=4)
    delivery_rating = models.IntegerField(choices=[(i,i) for i in range(1,6)], default=4)
    created_at      = models.DateTimeField(auto_now_add=True)
    is_approved     = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'restaurant', 'order')


# ── TableBooking ─────────────────────────────────
BOOKING_STATUS = [('pending','Pending'),('confirmed','Confirmed'),('cancelled','Cancelled'),('completed','Completed')]

class TableBooking(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='table_bookings')
    restaurant      = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='table_bookings')
    booking_date    = models.DateField()
    booking_time    = models.TimeField()
    num_guests      = models.IntegerField(default=2)
    name            = models.CharField(max_length=120)
    phone           = models.CharField(max_length=15)
    email           = models.EmailField()
    special_requests= models.TextField(blank=True)
    status          = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['-booking_date', '-booking_time']