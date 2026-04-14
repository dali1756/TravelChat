import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "*")

from core.settings import *  # noqa: E402, F401, F403

# 覆寫 ALLOWED_HOSTS 以允許測試 client（Django test client 使用 "testserver"）
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# 測試時使用 locmem backend（可透過 mail.outbox 檢查寄出信件）
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
