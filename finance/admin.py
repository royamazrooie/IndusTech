from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Transaction

# ۱. ثبت مدل کاربر سفارشی
admin.site.register(User, UserAdmin)

# ۲. ثبت مدل‌های مالی
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # کلمه type به category_type تغییر یافت
    list_display = ('name', 'category_type', 'is_active')
    list_filter = ('category_type', 'is_active')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # کلمه type به transaction_type تغییر یافت
    list_display = ('title', 'amount', 'transaction_type', 'category', 'created_by', 'date')
    list_filter = ('transaction_type', 'is_deleted')
    search_fields = ('title',)