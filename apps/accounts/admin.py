
from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "is_platform_admin",
        "is_active",
        "preferred_locale",
        "created_at",
    )
    search_fields = ("email", "full_name")
    list_filter = ("is_platform_admin", "is_active", "preferred_locale")
    ordering = ("email",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

