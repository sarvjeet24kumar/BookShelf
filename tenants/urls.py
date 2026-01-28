"""
URL configuration for tenants app.
Platform-level APIs for Super Admin.
"""
from django.urls import path
from tenants.views.tenant_views import (
    TenantListCreateView,
    TenantDetailView,
)

urlpatterns = [
    path('tenants/', TenantListCreateView.as_view(), name='tenant-list-create'),
    path('tenants/<uuid:id>/', TenantDetailView.as_view(), name='tenant-detail'),
]
