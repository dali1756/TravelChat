from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.models import SoftDeleteMixin
from members.managers import UserManager


class User(SoftDeleteMixin, AbstractUser):
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()
    all_objects = models.Manager()
