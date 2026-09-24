from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from finance.models import User, Category, Transaction
from decimal import Decimal

class FinanceAPITestCase(APITestCase):
    def setUp(self):
        """
        این متد قبل از اجرای هر تست یک‌بار اجرا می‌شود تا داده‌های اولیه را بسازد.
        """
        # ۱. ساخت کاربر (حسابدار)
        self.user = User.objects.create_user(
            username='test_accountant',
            password='strongpassword123',
            role=User.Role.ACCOUNTING_EMPLOYEE
        )
        
        # ۲. ساخت یک دسته‌بندی درآمدی
        self.income_category = Category.objects.create(
            name='فروش خدمات',
            category_type=Category.CategoryType.INCOME  # اصلاح شد
        )
        
        # ۳. ساخت یک دسته‌بندی هزینه‌ای
        self.expense_category = Category.objects.create(
            name='خرید تجهیزات',
            category_type=Category.CategoryType.EXPENSE  # اصلاح شد
        )

        # آدرس‌های API (با فرض اینکه basename در urls.py تنظیم شده باشد)
        self.transaction_url = reverse('transaction-list')

    def test_authentication_required(self):
        """
        تست امنیت: بررسی اینکه کاربر بدون لاگین نتواند لیست تراکنش‌ها را ببیند.
        """
        response = self.client.get(self.transaction_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_transaction_success(self):
        """
        تست ثبت تراکنش: بررسی ساخت موفق تراکنش با کاربر لاگین شده.
        """
        # احراز هویت (ورود کاربر)
        self.client.force_authenticate(user=self.user)
        
        data = {
            "transaction_type": "INCOME",  # اصلاح شد
            "title": "پروژه طراحی وب",
            "amount": 50000000,
            "category": self.income_category.id
        }
        
        response = self.client.post(self.transaction_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        # بررسی اینکه سازنده تراکنش به درستی توسط سیستم ثبت شده باشد
        self.assertEqual(Transaction.objects.first().created_by, self.user)

    def test_transaction_filtering(self):
        """
        تست فیلترها: بررسی صحت عملکرد فیلتر روی نوع تراکنش.
        """
        self.client.force_authenticate(user=self.user)
        
        # ایجاد دو تراکنش تستی (یکی درآمد، یکی هزینه)
        Transaction.objects.create(
            transaction_type='INCOME', title='درآمد ۱', amount=1000,  # اصلاح شد
            category=self.income_category, created_by=self.user
        )
        Transaction.objects.create(
            transaction_type='EXPENSE', title='هزینه ۱', amount=500,  # اصلاح شد
            category=self.expense_category, created_by=self.user
        )
        
        # ارسال درخواست با پارامتر فیلتر
        response = self.client.get(f"{self.transaction_url}?transaction_type=INCOME")  # اصلاح شد
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # باید فقط ۱ رکورد (درآمد) برگردد
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['transaction_type'], 'INCOME')  # اصلاح شد