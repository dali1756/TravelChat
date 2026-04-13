from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy

from members.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "username",
        "is_staff",
        "is_superuser",
        "last_login_time",
        "deleted_at",
    )
    search_fields = ("email", "username")
    ordering = ("email",)

    readonly_fields = ("created_at", "updated_at", "last_login_time", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (gettext_lazy("Personal info"), {"fields": ("username", "first_name", "last_name", "phone")}),
        (
            gettext_lazy("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            gettext_lazy("Timestamps"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "last_login_time",
                    "last_login",
                    "date_joined",
                    "deleted_at",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )
