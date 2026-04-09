from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from defects.views import DefectViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'defects', DefectViewSet, basename='defect')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),  
]