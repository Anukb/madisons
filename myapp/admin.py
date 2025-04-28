from django.contrib import admin
from .models import Plan, UserPlan, Transaction, Notification
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
    search_fields = ('name',)

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'plan__name')
    list_filter = ('is_active', 'plan')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'payment_method', 'created_at')
    search_fields = ('user__username', 'plan__name', 'payment_id')
    list_filter = ('payment_method', 'status')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('created_at',)




