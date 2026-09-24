from rest_framework import serializers
from .models import Category, Transaction
from django.contrib.auth import get_user_model

# ===================================================================
# Category Serializer
# ===================================================================
class CategorySerializer(serializers.ModelSerializer):
    # تغییر نام type به category_type با توجه به تغییرات فایل Models
    type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    
    class Meta:  # M باید حتماً بزرگ باشد
        model = Category
        # اصلاح نام فیلدها: type -> category_type و discription -> description
        fields = ['id', 'name', 'category_type', 'type_display', 'description', 'is_active']
        read_only_fields = ['id']

    def validate_name(self, value):
        if not value.strip():
            # در ولیدیشن‌ها ارور را raise می‌کنیم، نه return
            raise serializers.ValidationError('نام دسته نمی تواند خالی باشد')
        return value.strip()


# ===================================================================
# Transactions Serializer
# ===================================================================
class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    # تغییر category.type به category.category_type
    category_type = serializers.CharField(source='category.category_type', read_only=True)
    # تغییر get_type_display به get_transaction_type_display
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    # نمایش نام کاربری ثبت‌کننده (به جای فرستادن کل آبجکت کاربر یا فقط ID)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:  # M باید حتماً بزرگ باشد
        model = Transaction
        # حرف اول fields باید کوچک باشد
        # فیلدهای name و created time وجود نداشتند و پاک شدند. description به descriptions تغییر یافت.
        fields = [
            'id', 'transaction_type', 'title', 'amount', 'category', 
            'category_name', 'category_type', 'type_display', 
            'created_by', 'created_by_username', 'date', 
            'created_time', 'description', 'is_deleted'
        ]
        read_only_fields = [
            'id', 'type_display', 'category_name', 'category_type',
            'created_by_username', 'created_time', 'is_deleted','created_by'
        ]

    def validate_amount(self, value):
        if value <= 0:
            # ارور را raise می‌کنیم
            raise serializers.ValidationError('مبلغ تراکنش باید حتما عددی مثبت و بزرگ تر از صفر باشد')
        return value
    
    def validate_category(self, value):
        # check if the category of this transaction isn't deleted
        if not value.is_active:
            raise serializers.ValidationError(f'دسته‌بندی با نام "{value.name}" غیرفعال شده است')
        return value

    def validate(self, data):
        """
        اعتبارسنجی سطح کل آبجکت (Cross-Field Validation):
        بررسی تطابق منطقی بین «نوع تراکنش» و «نوع دسته‌بندی» انتخابی
        """
        # تغییر type به transaction_type
        transaction_type = data.get('transaction_type', getattr(self.instance, 'transaction_type', None))
        category = data.get('category', getattr(self.instance, 'category', None))

        if transaction_type and category:
            # ۱. تراکنش‌های ورودی (INCOME / RECEIPT)
            if transaction_type in [Transaction.TransactionType.INCOME, Transaction.TransactionType.RECEIPT]:
                if category.category_type != Category.CategoryType.INCOME:
                    raise serializers.ValidationError({
                        "category": f"خطای عدم تطابق: برای تراکنش‌های نوع «{Transaction.TransactionType(transaction_type).label}»، باید دسته‌بندی با ماهیت «درآمد» انتخاب کنید."
                    })

            # ۲. تراکنش‌های خروجی (EXPENSE / PAYMENT)
            # از آنجا که در فایل models کلمه EXPENSES را به EXPENSE تغییر دادیم، اینجا هم اصلاح شد
            elif transaction_type in [Transaction.TransactionType.EXPENSE, Transaction.TransactionType.PAYMENT]:
                if category.category_type != Category.CategoryType.EXPENSE:
                    raise serializers.ValidationError({
                        "category": f"خطای عدم تطابق: برای تراکنش‌های نوع «{Transaction.TransactionType(transaction_type).label}»، باید دسته‌بندی با ماهیت «هزینه» انتخاب کنید."
                    })

        return data

# getting user info serializer
user = get_user_model()
class UserSreializer(serializers.ModelSerializer):
    class Meta :
        model = user
        fields = ['id','username','email','first_name','last_name']
