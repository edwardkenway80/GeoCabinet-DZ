

import uuid
import apps.accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "email",
                    models.EmailField(max_length=254),
                ),
                (
                    "password",
                    models.TextField(db_column="password_hash"),
                ),
                (
                    "full_name",
                    models.CharField(max_length=180),
                ),
                (
                    "is_platform_admin",
                    models.BooleanField(default=False),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True),
                ),
                (
                    "preferred_locale",
                    models.CharField(default="fr", max_length=5),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "db_table": '"gc"."users"',
                "managed": False,
            },
            managers=[
                ("objects", apps.accounts.models.CustomUserManager()),
            ],
        ),
    ]
