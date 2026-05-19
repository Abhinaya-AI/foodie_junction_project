from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, Restaurant, FoodItem, Cart, CartItem, Order, OrderItem, Review, TableBooking


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ('email','name','phone','is_staff','date_joined')
    list_filter    = ('is_staff','is_active')
    search_fields  = ('email','name')
    ordering       = ('-date_joined',)
    fieldsets      = (
        (None, {'fields': ('email','password')}),
        ('Info', {'fields': ('name','phone','avatar')}),
        ('Permissions', {'fields': ('is_active','is_staff','is_superuser')}),
    )
    add_fieldsets  = ((None, {'classes':('wide',), 'fields':('email','password1','password2')}),)
    filter_horizontal = ()

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email','otp_code','created_at','expires_at','is_used')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display  = ('name','city','rating','is_pure_veg','serves_alcohol','is_open','is_featured')
    list_filter   = ('city','is_pure_veg','serves_alcohol','is_open')
    list_editable = ('is_open','is_featured')
    search_fields = ('name',)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display  = ('name','restaurant','category','price','is_veg','is_bestseller','is_available')
    list_filter   = ('category','is_veg','is_available')
    list_editable = ('is_available','is_bestseller')
    search_fields = ('name','restaurant__name')

class OrderItemInline(admin.TabularInline):
    model = OrderItem; extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','restaurant','status','payment_method','total_amount','created_at')
    list_filter  = ('status','payment_method','payment_status')
    inlines      = [OrderItemInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('user','restaurant','rating','is_approved','created_at')
    list_editable = ('is_approved',)

@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ('name','restaurant','booking_date','booking_time','num_guests','status')

admin.site.site_header  = "🍔 Foodie Junction Admin"
admin.site.site_title   = "Foodie Junction"
admin.site.index_title  = "Dashboard"