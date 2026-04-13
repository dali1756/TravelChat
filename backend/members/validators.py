import re

from django.core.exceptions import ValidationError


class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError("密碼必須包含至少一個大寫字母。")

    def get_help_text(self):
        return "密碼必須包含至少一個大寫字母。"


class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r"[a-z]", password):
            raise ValidationError("密碼必須包含至少一個小寫字母。")

    def get_help_text(self):
        return "密碼必須包含至少一個小寫字母。"


class DigitValidator:
    def validate(self, password, user=None):
        if not re.search(r"\d", password):
            raise ValidationError("密碼必須包含至少一個數字。")

    def get_help_text(self):
        return "密碼必須包含至少一個數字。"


class SpecialCharValidator:
    def validate(self, password, user=None):
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", password):
            raise ValidationError("密碼必須包含至少一個特殊符號。")

    def get_help_text(self):
        return "密碼必須包含至少一個特殊符號。"
