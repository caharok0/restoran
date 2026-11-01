from django.contrib import admin

from .models import Category, Order, OrderItem, Review

admin.site.register(Category)


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ('dish_name', 'unit_price', 'quantity')
	can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer_name', 'phone', 'total', 'payment_method', 'status', 'created_at')
	list_filter = ('status', 'payment_method', 'created_at')
	search_fields = ('customer_name', 'phone', 'email', 'delivery_address')
	readonly_fields = ('total', 'created_at')
	inlines = (OrderItemInline,)


@admin.action(description='Схвалити вибрані відгуки')
def approve_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description='Приховати вибрані відгуки')
def hide_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('dish', 'user', 'rating', 'created_at', 'is_approved')
	list_filter = ('is_approved', 'rating', 'created_at')
	search_fields = ('dish__name', 'user__username', 'comment')
	list_editable = ('is_approved',)
	readonly_fields = ('created_at',)
	actions = (approve_reviews, hide_reviews)
