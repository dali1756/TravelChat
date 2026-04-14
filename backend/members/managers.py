from django.contrib.auth.models import BaseUserManager

from core.models import SoftDeleteManager


class UserManager(SoftDeleteManager, BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        # 註冊流程預設 is_active = False（需經 email 驗證才能登入）
        # 如果 request 有帶入 is_active 則依其設定
        extra_fields.setdefault("is_active", False)
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # superuser 可立即登入
        extra_fields["is_active"] = True
        return self.create_user(email, username, password, **extra_fields)

    def public(self):
        """
        對外 API 專用的 queryset。
        隱藏管理員帳號：
        - 排除 `is_superuser=True` 的帳號。
        - 額外排除 username 大小寫不敏感等於 "admin" 的帳號。
        """
        return self.get_queryset().filter(is_superuser=False).exclude(username__iexact="admin")
