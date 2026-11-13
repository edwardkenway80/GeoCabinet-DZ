import uuid

from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not full_name:
            raise ValueError("Full name is required")

        user = self.model(
            email=email.strip().lower(),
            full_name=full_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_platform_admin", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_platform_admin"]:
            raise ValueError("Superuser must be a platform admin")

        return self.create_user(email, full_name, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email.strip().lower())


class CustomUser(AbstractBaseUser):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    email = models.EmailField(max_length=254)
    password = models.TextField(db_column="password_hash")
    last_login = None

    full_name = models.CharField(max_length=180)
    is_platform_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    preferred_locale = models.CharField(max_length=5, default="fr")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    @property
    def is_superuser(self):
        return self.is_platform_admin

    @property
    def is_staff(self):
        return self.is_platform_admin

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_platform_admin

    def has_module_perms(self, app_label):
        return self.is_active and self.is_platform_admin

    def __str__(self):
        return self.email

    class Meta:
        db_table = '"gc"."users"'
        managed = False
