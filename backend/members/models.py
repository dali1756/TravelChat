from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from core.models import SoftDeleteMixin
from members.managers import UserManager


class User(SoftDeleteMixin, AbstractUser):
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_time = models.DateTimeField(null=True, blank=True, default=None)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()
    all_objects = models.Manager()
