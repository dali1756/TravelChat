import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


def _build_url(path: str, uid: str, token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/{path.lstrip('/')}?uid={uid}&token={token}"


def _send(subject: str, body: str, to_email: str) -> None:
    try:
        EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        ).send(fail_silently=False)
    except Exception:  # noqa: BLE001
        logger.exception("寄送 email 失敗 to=%s subject=%s", to_email, subject)


def send_verification_email(user) -> None:
    """
    寄送 email 驗證信，寄信失敗不中斷註冊流程
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    url = _build_url("verify-email", uid, token)
    body = f"您好 {user.username}，\n\n請點擊以下連結完成 email 驗證：\n{url}\n\n如非本人操作請忽略此信。"
    _send("請完成您的 email 驗證", body, user.email)


def send_password_reset_email(user) -> None:
    """
    寄送忘記密碼重設信，寄信失敗不中斷請求流程。
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    url = _build_url("reset-password", uid, token)
    body = f"您好 {user.username}，\n\n請點擊以下連結重設您的密碼：\n{url}\n\n如非本人操作請忽略此信，密碼不會被變更。"
    _send("重設您的密碼", body, user.email)
