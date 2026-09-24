from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

# -------------------------------------------------------------------
# Custom User Model
# -------------------------------------------------------------------
class User(AbstractUser):
    class Role(models.TextChoices):
        ACCOUNTING_EMPLOYEE = 'ACCOUNTING', 'Accounting employee'
        ADMIN = 'ADMIN', 'Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ACCOUNTING_EMPLOYEE,
        verbose_name="نقش کاربری",
    )

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    # مثال برای Soft Delete در آینده:
    # def delete(self, *args, **kwargs):
    #     self.is_active = False
    #     self.save()

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'


# -------------------------------------------------------------------
# Transactions Category Model
# -------------------------------------------------------------------
class Category(models.Model):
    class CategoryType(models.TextChoices):
        INCOME = 'INCOME', 'درآمد'
        EXPENSE = 'EXPENSE', 'هزینه'

    name = models.CharField(
        max_length=100,
        verbose_name='نام دسته بندی'
    )

    category_type = models.CharField(
        max_length=12,
        choices=CategoryType.choices,
        verbose_name='نوع دسته بندی'
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='توضیحات کوتاه'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    class Meta:
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'
        ordering = ['-id']

    def __str__(self):
        if self.description:
            return f"نام = {self.name} | نوع = {self.get_category_type_display()} | توضیحات = {self.description}"
        return f"نام = {self.name} | نوع = {self.get_category_type_display()}"


# -------------------------------------------------------------------
# Transactions Model
# -------------------------------------------------------------------
class Transaction(models.Model):
    """
    مدل تراکنش‌های مالی سیستم.
    شامل ولیدیتور برای جلوگیری از مبالغ منفی و صفر، و حفاظت از حذف داده‌های متصل.
    """
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'درآمد'
        EXPENSE = 'EXPENSE', 'هزینه'
        RECEIPT = 'RECEIPT', 'دریافت (ورود نقدینگی)'
        PAYMENT = 'PAYMENT', 'پرداخت (خروج نقدینگی)'

    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name='نوع تراکنش',
    )

    title = models.CharField(
        max_length=150,
        verbose_name='عنوان'
    )

    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='مبلغ (ریال)'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='دسته بندی تراکنش'
    )

    created_by = models.ForeignKey(
        'User', 
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='سازنده این تراکنش'
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name='تاریخ تراکنش'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات تکمیلی'
    )

    created_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ثبت تراکنش'
    )

    # --- فیلدهای مربوط به حذف منطقی (Soft Delete) ---
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="حذف شده؟"
    )

    delete_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ حذف"
    )

    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,  # اصلاح شد به SET_NULL
        related_name='delete_item_logs',
        null=True,
        blank=True,
        verbose_name='کاربر حذف‌کننده'
    )

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-date', '-created_time']

    def __str__(self):
        return f"{self.title} | {self.amount} | {self.get_transaction_type_display()}"