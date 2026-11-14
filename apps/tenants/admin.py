
from django.contrib import admin
from .models import Tenant, TenantMembership, ProfessionalProfile


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tenant)
class TenantAdmin(ReadOnlyAdmin):
    list_display = ("name", "slug", "status", "default_locale", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("status", "default_locale")
    ordering = ("name",)


@admin.register(TenantMembership)
class TenantMembershipAdmin(ReadOnlyAdmin):
    list_display = ("tenant", "user", "role_code", "is_active", "joined_at")
    search_fields = ("tenant__name", "user__email")
    list_filter = ("role_code", "is_active")
    ordering = ("tenant__name",)


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(ReadOnlyAdmin):
    list_display = (
        "tenant",
        "membership",
        "professional_type",
        "registration_number",
        "authorization_valid_until",
    )
    search_fields = ("registration_number", "authorization_reference")
    list_filter = ("professional_type",)

