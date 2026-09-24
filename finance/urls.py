from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, DashboardAPIView , FinancialReportAPIView , UserProfileView

router = DefaultRouter()
# بر اساس استانداردهای REST، نام مسیرها با حروف کوچک نوشته شد
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('reports/', FinancialReportAPIView.as_view(), name='reports'),

    # با این خط، تمام مسیرهای استاندارد CRUD به پروژه اضافه می‌شوند
    path('', include(router.urls)),
    # url ie ke profile info ro mifreste braye front
    path('profile/me/',UserProfileView.as_view(),name='user_profile_info')
    
]