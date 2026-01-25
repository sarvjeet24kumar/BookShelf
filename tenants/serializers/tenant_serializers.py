"""
Serializers for Tenant model.
Used by Super Admin for platform-level tenant management.
"""
from rest_framework import serializers
from tenants.models import Tenant
from tenants.constants import MAX_TENANT_NAME_LENGTH, MAX_TENANT_SLUG_LENGTH


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for listing tenants.
    """
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'is_active',
            'subscription_plan',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TenantDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for tenant details.
    """
    user_count = serializers.SerializerMethodField()
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'is_active',
            'subscription_plan',
            'created_at',
            'updated_at',
            'user_count',
            'book_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):

        return obj.users.filter(deleted_at__isnull=True).count()
    
    def get_book_count(self, obj):
        return obj.books.filter(deleted_at__isnull=True).count()


class TenantCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new tenant.
    """
    
    class Meta:
        model = Tenant
        fields = [
            'name',
            'slug',
            'is_active',
            'subscription_plan',
        ]
    
    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value
    
    def validate_slug(self, value):
        value = value.strip().lower()
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A tenant with this slug already exists.")
        return value


class TenantUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a tenant.
   
    """
    
    class Meta:
        model = Tenant
        fields = [
            'name',
            'is_active',
            'subscription_plan',
        ]
    
    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value
