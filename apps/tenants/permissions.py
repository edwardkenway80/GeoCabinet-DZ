from rest_framework import permissions
from .selectors import get_user_membership

class IsTenantMember(permissions.BasePermission):
    """
    يسمح فقط للأعضاء النشطين في المكتب بالوصول.
    يقوم بجلب العضوية وتخزينها في request.membership للاستخدام لاحقاً.
    """
    def has_permission(self, request, view):
        tenant_id = view.kwargs.get('tenant_id')
        if not tenant_id:
            return True # سيتم التحقق منها في الـ View
            
        membership = get_user_membership(request.user, tenant_id)
        if not membership:
            return False
            
        request.membership = membership
        return True

class IsTenantAdmin(IsTenantMember):
    """
    يسمح فقط للمالك (owner) أو المدير (expert_director) بإدارة المكتب.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.membership.role_code in ['owner', 'expert_director']