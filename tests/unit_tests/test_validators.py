import pytest

from src.validators import validate_email_russian, validate_password_russian


# ──── Email ────────────────────────────────────────────────────────────────

class TestValidateEmailRussian:
    def test_valid_email(self):
        assert validate_email_russian("User@Example.COM") == "User@Example.COM"

    def test_strips_whitespace(self):
        assert validate_email_russian("  test@mail.ru  ") == "test@mail.ru"

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="строкой"):
            validate_email_russian(123)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            validate_email_russian("   ")

    def test_missing_at_raises(self):
        with pytest.raises(ValueError, match="@"):
            validate_email_russian("notanemail")

    def test_empty_local_part_raises(self):
        with pytest.raises(ValueError, match="перед символом @"):
            validate_email_russian("@domain.com")

    def test_empty_domain_raises(self):
        with pytest.raises(ValueError, match="после символа @"):
            validate_email_russian("user@")

    def test_domain_without_dot_raises(self):
        with pytest.raises(ValueError, match="домен"):
            validate_email_russian("user@nodot")

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError, match="формат"):
            validate_email_russian("user@.com")


# ──── Password ─────────────────────────────────────────────────────────────

class TestValidatePasswordRussian:
    def test_valid_password(self):
        assert validate_password_russian("Abc12345") == "Abc12345"

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="строкой"):
            validate_password_russian(12345678)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            validate_password_russian("")

    def test_only_spaces_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            validate_password_russian("   ")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="8 символов"):
            validate_password_russian("Ab1")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="100 символов"):
            validate_password_russian("Aa1" + "x" * 99)

    def test_no_uppercase_raises(self):
        with pytest.raises(ValueError, match="заглавную"):
            validate_password_russian("abcde123")

    def test_no_lowercase_raises(self):
        with pytest.raises(ValueError, match="строчную"):
            validate_password_russian("ABCDE123")

    def test_no_digit_raises(self):
        with pytest.raises(ValueError, match="цифру"):
            validate_password_russian("AbcdefGH")

    def test_spaces_raises(self):
        with pytest.raises(ValueError, match="пробелы"):
            validate_password_russian("Abc 1234")
