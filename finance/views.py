from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from django.db.models import Sum, Count, Q
from django.utils.dateparse import parse_date
from django.utils import timezone

from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer ,UserSreializer

from django.db.models.functions import TruncDate , TruncYear , TruncMonth

# ===================================================================
# Filters
# ===================================================================
class TransactionFilter(filters.FilterSet): # FilterSet باید با حروف بزرگ باشد
    from_date = filters.DateFilter(field_name='date', lookup_expr='gte', label='از تاریخ')
    # lte مخفف less than or equal است (نه lse)
    to_date = filters.DateFilter(field_name='date', lookup_expr='lte', label='تا تاریخ')
    
    class Meta: # M باید بزرگ باشد
        model = Transaction
        # نوع تراکنش به transaction_type تغییر یافت
        fields = ['transaction_type', 'category', 'from_date', 'to_date']

# ===================================================================
# ViewSets
# ===================================================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all() # پرانتز جا مانده بود
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_class = TransactionFilter
    search_fields = ['title'] # غلط املایی اصلاح شد و با حروف کوچک
    ordering_fields = ['date', 'amount']
    ordering = ['-date']

    def get_queryset(self):
        """بازنویسی کوئری‌ست برای نادیده گرفتن تراکنش‌های حذف شده (Soft Delete)"""
        return Transaction.objects.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_by = self.request.user
        instance.delete_date = timezone.now() # نام فیلد در مدل delete_date بود نه deleted_date
        instance.save()

# ===================================================================
# API Views
# ===================================================================
class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        valid_transactions = Transaction.objects.filter(is_deleted=False)
        
        # در ویوهای همگام (Sync) باید از aggregate استفاده کنیم نه aaggregate
        aggregations = valid_transactions.aggregate(
            total_income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME)),
            total_expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE)),
            total_receipt=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.RECEIPT)),
            total_payment=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.PAYMENT)),
            total_count=Count('id')
        )
        
        total_income = aggregations['total_income'] or 0
        total_expense = aggregations['total_expense'] or 0
        total_receipt = aggregations['total_receipt'] or 0
        total_payment = aggregations['total_payment'] or 0

        # سود خالص
        net_profit = total_income - total_expense
        # مانده نقدینگی (دریافتی‌ها منهای پرداختی‌ها)
        cash_flow_balance = total_receipt - total_payment
        
        last_five_transactions = valid_transactions.order_by('-date', '-created_time')[:5]
        serializer = TransactionSerializer(last_five_transactions, many=True)

        return Response({
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "total_receipt": total_receipt,
                "total_payment": total_payment,
            },
            "balances": {
                "net_profit": net_profit,
                "cash_flow_balance": cash_flow_balance
            },
            "total_transactions_count": aggregations['total_count'],
            "recent_transactions": serializer.data
        })
    
class FinancialReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        # 1. کوئری پایه (برای محاسبه باقیمانده کل تاریخ)
        base_qs = Transaction.objects.filter(is_deleted=False)
        
        qs = base_qs
        parse_from = None
        parse_to = None

        if from_date:
            parse_from = parse_date(from_date)
            if parse_from:
                qs = qs.filter(date__gte=parse_from)
        if to_date:
            parse_to = parse_date(to_date)
            if parse_to:
                qs = qs.filter(date__lte=parse_to)

        # ==========================================
        # بخش اول و دوم: خلاصه‌ی مالی و رتبه‌بندی دسته‌ها
        # ==========================================
        period_totals = qs.aggregate(
            total_income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME)),
            total_expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE)),
            total_receipt=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.RECEIPT)),
            total_payment=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.PAYMENT)),
        )
        
        t_income = period_totals['total_income'] or 0
        t_expense = period_totals['total_expense'] or 0
        t_receipt = period_totals['total_receipt'] or 0
        t_payment = period_totals['total_payment'] or 0

        all_time_totals = base_qs.aggregate(
            total_rec=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.RECEIPT)),
            total_pay=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.PAYMENT)),
        )
        overall_balance = (all_time_totals['total_rec'] or 0) - (all_time_totals['total_pay'] or 0)

        category_reports = list(qs.values(
            'category__id', 'category__name', 'category__category_type'
        ).annotate(
            total_amount=Sum('amount'),
            transactions_count=Count('id')
        ).order_by('-total_amount'))

        for cat in category_reports:
            amount = cat['total_amount']
            if cat['category__category_type'] == 'EXPENSE' and t_expense > 0:
                cat['percentage'] = round((amount / t_expense) * 100, 1)
            elif cat['category__category_type'] == 'INCOME' and t_income > 0:
                cat['percentage'] = round((amount / t_income) * 100, 1)
            else:
                cat['percentage'] = 0

        # ==========================================
        # بخش سوم: دیتای نمودار ستونی هوشمند
        # ==========================================
        # تعیین مقیاس نمودار بر اساس بازه زمانی
        trunc_function = TruncDate('date') # پیش‌فرض: روزانه
        
        if not from_date and not to_date:
            # کل دوره -> سالانه
            trunc_function = TruncYear('date')
        elif parse_from:
            # اگر فرانت‌اند فیلتر زمانی فرستاده بود، اختلاف روزها را حساب می‌کنیم
            end_date = parse_to if parse_to else timezone.now().date()
            delta_days = (end_date - parse_from).days
            
            if delta_days > 366:
                # بیشتر از یک سال -> سالانه
                trunc_function = TruncYear('date')
            elif delta_days > 45:
                # بین یک و نیم ماه تا یک سال -> ماهانه
                trunc_function = TruncMonth('date')

        # گروه‌بندی دیتا با مقیاسی که در بالا تشخیص داده شد
        chart_data = qs.annotate(period=trunc_function).values('period').annotate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME)),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE))
        ).order_by('period')

        formatted_chart = [
            {
                "date": entry['period'],
                "income": entry['income'] or 0,
                "expense": entry['expense'] or 0
            }
            for entry in chart_data
        ]

        return Response({
            "summary": {
                "total_income": t_income,
                "total_expense": t_expense,
                "net_profit": t_income - t_expense,
                "cash_flow": t_receipt - t_payment,
                "overall_balance": overall_balance
            },
            "category_ranking": category_reports,
            "chart_data": formatted_chart
        })

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        serializer = UserSreializer(request.user)
        return Response(serializer.data)