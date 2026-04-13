import pytest
from django.core.exceptions import ValidationError

from members.validators import (
    DigitValidator,
    LowercaseValidator,
    SpecialCharValidator,
    UppercaseValidator,
)


class TestUppercaseValidator:
    def test_valid(self):
        UppercaseValidator().validate("Aa1!xy")

    def test_missing(self):
        with pytest.raises(ValidationError):
            UppercaseValidator().validate("aa1!xy")


class TestLowercaseValidator:
    def test_valid(self):
        LowercaseValidator().validate("Aa1!xy")

    def test_missing(self):
        with pytest.raises(ValidationError):
            LowercaseValidator().validate("AA1!XY")


class TestDigitValidator:
    def test_valid(self):
        DigitValidator().validate("Aa1!xy")

    def test_missing(self):
        with pytest.raises(ValidationError):
            DigitValidator().validate("Aa!xyz")


class TestSpecialCharValidator:
    def test_valid(self):
        SpecialCharValidator().validate("Aa1!xy")

    def test_missing(self):
        with pytest.raises(ValidationError):
            SpecialCharValidator().validate("Aa1xyz")


class TestMinimumLength:
    def test_too_short(self):
        """Django MinimumLengthValidator is configured with min_length=6 in settings."""
        from django.contrib.auth.password_validation import validate_password

        with pytest.raises(ValidationError):
            validate_password("Aa1!x")

    def test_valid_length(self):
        from django.contrib.auth.password_validation import validate_password

        validate_password("Aa1!xy")
