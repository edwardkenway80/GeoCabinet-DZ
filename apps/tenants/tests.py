from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.services.core import create_tenant_with_owner, add_tenant_member
from apps.tenants.selectors import get_user_tenants, get_user_membership

User = get_user_model()


class TenantBusinessLogicTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="owner@test.com", full_name="Owner User", password="password123"
        )
        self.user2 = User.objects.create_user(
            email="staff@test.com", full_name="Staff User", password="password123"
        )

    def test_create_tenant_with_owner(self):
        tenant = create_tenant_with_owner(
            name="مكتب الخبرة", slug="expert-office", user=self.user1
        )
        self.assertEqual(tenant.name, "مكتب الخبرة")
        self.assertEqual(tenant.memberships.count(), 1)
        self.assertEqual(tenant.memberships.first().user, self.user1)
        self.assertEqual(tenant.memberships.first().role_code, 'owner')

    def test_duplicate_slug_fails(self):
        create_tenant_with_owner(name="مكتب 1", slug="office-1", user=self.user1)
        with self.assertRaises(ValidationError):
            create_tenant_with_owner(name="مكتب 2", slug="office-1", user=self.user2)

    def test_add_member(self):
        tenant = create_tenant_with_owner(name="مكتب", slug="office", user=self.user1)
        membership = add_tenant_member(tenant=tenant, user=self.user2, role_code="surveyor")
        self.assertEqual(membership.role_code, "surveyor")
        self.assertTrue(membership.is_active)

    def test_prevent_duplicate_member(self):
        tenant = create_tenant_with_owner(name="مكتب", slug="office", user=self.user1)
        with self.assertRaises(ValidationError):
            add_tenant_member(tenant=tenant, user=self.user1, role_code="surveyor")

    def test_add_member_invalid_role_fails(self):
        tenant = create_tenant_with_owner(name="مكتب", slug="office-r", user=self.user1)
        with self.assertRaises(ValidationError):
            add_tenant_member(tenant=tenant, user=self.user2, role_code="god_mode")


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="user_a@test.com", full_name="User A", password="password123"
        )
        self.user_b = User.objects.create_user(
            email="user_b@test.com", full_name="User B", password="password123"
        )
        self.tenant_a = create_tenant_with_owner(name="مكتب أ", slug="office-a", user=self.user_a)
        self.tenant_b = create_tenant_with_owner(name="مكتب ب", slug="office-b", user=self.user_b)

    def test_user_sees_only_own_tenants(self):
        user_a_tenants = get_user_tenants(self.user_a)
        self.assertIn(self.tenant_a, user_a_tenants)
        self.assertNotIn(self.tenant_b, user_a_tenants)

        user_b_tenants = get_user_tenants(self.user_b)
        self.assertIn(self.tenant_b, user_b_tenants)
        self.assertNotIn(self.tenant_a, user_b_tenants)

    def test_user_cannot_access_other_tenant_membership(self):
        membership = get_user_membership(self.user_a, self.tenant_b.id)
        self.assertIsNone(membership)

    def test_inactive_membership_denied(self):
        TenantMembership.objects.filter(tenant=self.tenant_a, user=self.user_a).update(is_active=False)
        membership = get_user_membership(self.user_a, self.tenant_a.id)
        self.assertIsNone(membership)
