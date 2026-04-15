"""Unit tests for AuthService — covers all 11 methods."""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from src.exceptions import (
    EmailNotRegisteredException,
    ExpiredTokenException,
    IncorrectPasswordException,
    IncorrectTokenException,
    InvalidRefreshTokenException,
    ObjectAlreadyExistsException,
    SameEmailException,
    UserAlreadyExistsException,
    UserNotAuthenticatedException,
)
from src.services.auth import AuthService


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_db(**overrides):
    db = MagicMock()
    db.users = AsyncMock()
    db.commit = AsyncMock()
    for k, v in overrides.items():
        setattr(db, k, v)
    return db


def _make_blacklist(is_blacklisted_value: bool = False):
    bl = AsyncMock()
    bl.add = AsyncMock()
    bl.is_blacklisted = AsyncMock(return_value=is_blacklisted_value)
    return bl


def _make_service(db=None, blacklist=None):
    return AuthService(db=db or _make_db(), blacklist=blacklist)


SECRET = "test-secret-key"
ALGORITHM = "HS256"


def _encode_token(payload: dict, secret: str = SECRET) -> str:
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


# ─── Token creation ──────────────────────────────────────────────────────────


@patch("src.services.auth.settings")
def test_create_access_token(mock_settings):
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    token = svc.create_access_token({"user_id": 1, "is_admin": False})
    decoded = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    assert decoded["user_id"] == 1
    assert decoded["type"] == "access"
    assert "exp" in decoded


@patch("src.services.auth.settings")
def test_create_refresh_token(mock_settings):
    mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 30
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    token = svc.create_refresh_token({"user_id": 1})
    decoded = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    assert decoded["user_id"] == 1
    assert decoded["type"] == "refresh"


# ─── Password hashing ────────────────────────────────────────────────────────


def test_hash_and_verify_password():
    svc = _make_service()
    hashed = svc.hash_password("StrongPass123")
    assert hashed != "StrongPass123"
    assert svc.verify_password("StrongPass123", hashed) is True
    assert svc.verify_password("WrongPass", hashed) is False


# ─── Token decoding ──────────────────────────────────────────────────────────


@patch("src.services.auth.settings")
def test_decode_token_success(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = _encode_token(payload)
    result = svc.decode_token(token)
    assert result["user_id"] == 1


@patch("src.services.auth.settings")
def test_decode_token_expired(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = _encode_token(payload)
    with pytest.raises(ExpiredTokenException):
        svc.decode_token(token)


@patch("src.services.auth.settings")
def test_decode_token_invalid(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None
    svc = _make_service()

    with pytest.raises(IncorrectTokenException):
        svc.decode_token("totally.invalid.token")


@patch("src.services.auth.settings")
def test_decode_token_key_rotation(mock_settings):
    """Token signed with old key should decode via JWT_SECRET_KEY_PREVIOUS."""
    old_secret = "old-secret"
    mock_settings.JWT_SECRET_KEY = "new-secret"
    mock_settings.JWT_SECRET_KEY_PREVIOUS = old_secret
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = _encode_token(payload, secret=old_secret)
    result = svc.decode_token(token)
    assert result["user_id"] == 1


@patch("src.services.auth.settings")
def test_decode_token_expired_with_old_key(mock_settings):
    """Expired token with old key should raise ExpiredTokenException."""
    old_secret = "old-secret"
    mock_settings.JWT_SECRET_KEY = "new-secret"
    mock_settings.JWT_SECRET_KEY_PREVIOUS = old_secret
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = _encode_token(payload, secret=old_secret)
    with pytest.raises(ExpiredTokenException):
        svc.decode_token(token)


@patch("src.services.auth.settings")
def test_decode_token_invalid_both_keys(mock_settings):
    """Token invalid for both keys should raise IncorrectTokenException."""
    mock_settings.JWT_SECRET_KEY = "new-secret"
    mock_settings.JWT_SECRET_KEY_PREVIOUS = "old-secret"
    mock_settings.JWT_ALGORITHM = ALGORITHM
    svc = _make_service()

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = _encode_token(payload, secret="completely-wrong-secret")
    with pytest.raises(IncorrectTokenException):
        svc.decode_token(token)


# ─── Register ────────────────────────────────────────────────────────────────


async def test_register_user_success():
    db = _make_db()
    mock_user = MagicMock(id=1, email="test@example.com")
    db.users.add.return_value = mock_user
    svc = _make_service(db)

    from src.schemas.users import UserRequestAdd

    result = await svc.register_user(
        UserRequestAdd(email="test@example.com", password="Strong1pass")
    )
    assert result is mock_user
    db.users.add.assert_called_once()
    db.commit.assert_called_once()


async def test_register_user_duplicate():
    db = _make_db()
    db.users.add.side_effect = ObjectAlreadyExistsException()
    svc = _make_service(db)

    from src.schemas.users import UserRequestAdd

    with pytest.raises(UserAlreadyExistsException):
        await svc.register_user(UserRequestAdd(email="dup@example.com", password="Strong1pass"))


# ─── Login ───────────────────────────────────────────────────────────────────


@patch("src.services.auth.settings")
async def test_login_user_success(mock_settings):
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 30
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM

    db = _make_db()
    svc = _make_service(db)
    hashed = svc.hash_password("Strong1pass")
    mock_user = MagicMock(id=1, email="user@example.com", hashed_password=hashed, is_admin=False)
    db.users.get_user_with_hashed_password.return_value = mock_user

    from src.schemas.users import UserRequestAdd

    access, refresh = await svc.login_user(
        UserRequestAdd(email="user@example.com", password="Strong1pass")
    )
    assert access
    assert refresh


async def test_login_user_email_not_found():
    from sqlalchemy.exc import NoResultFound

    db = _make_db()
    db.users.get_user_with_hashed_password.side_effect = NoResultFound()
    svc = _make_service(db)

    from src.schemas.users import UserRequestAdd

    with pytest.raises(EmailNotRegisteredException):
        await svc.login_user(UserRequestAdd(email="noone@example.com", password="Strong1pass"))


async def test_login_user_wrong_password():
    db = _make_db()
    svc = _make_service(db)
    hashed = svc.hash_password("CorrectPass1")
    mock_user = MagicMock(hashed_password=hashed)
    db.users.get_user_with_hashed_password.return_value = mock_user

    from src.schemas.users import UserRequestAdd

    with pytest.raises(IncorrectPasswordException):
        await svc.login_user(UserRequestAdd(email="user@example.com", password="WrongPass1x"))


# ─── Logout ──────────────────────────────────────────────────────────────────


@patch("src.services.auth.settings")
async def test_logout_success(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    bl = _make_blacklist()
    svc = _make_service(blacklist=bl)

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = _encode_token(payload)
    refresh_payload = {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(days=30)}
    refresh_token = _encode_token(refresh_payload)

    await svc.logout_user(token, refresh_token)
    assert bl.add.call_count == 2  # access + refresh


@patch("src.services.auth.settings")
async def test_logout_expired_access_allowed(mock_settings):
    """Logout with expired access token should succeed without error."""
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    bl = _make_blacklist()
    svc = _make_service(blacklist=bl)

    payload = {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = _encode_token(payload)
    await svc.logout_user(token)
    # No blacklist call for expired token
    bl.add.assert_not_called()


async def test_logout_empty_token():
    svc = _make_service()
    with pytest.raises(UserNotAuthenticatedException):
        await svc.logout_user("")


@patch("src.services.auth.settings")
async def test_logout_invalid_token(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    svc = _make_service()
    with pytest.raises(UserNotAuthenticatedException):
        await svc.logout_user("totally.invalid.token")


# ─── Refresh ─────────────────────────────────────────────────────────────────


@patch("src.services.auth.settings")
async def test_refresh_success(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 30

    db = _make_db()
    mock_user = MagicMock(id=1, is_admin=False)
    db.users.get_one_or_none.return_value = mock_user
    bl = _make_blacklist(is_blacklisted_value=False)
    svc = _make_service(db, blacklist=bl)

    payload = {
        "user_id": 1,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    refresh_token = _encode_token(payload)
    new_access, new_refresh = await svc.refresh_access_token(refresh_token)
    assert new_access
    assert new_refresh
    bl.add.assert_called_once()  # old refresh token blacklisted


@patch("src.services.auth.settings")
async def test_refresh_expired_token(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    svc = _make_service()
    payload = {
        "user_id": 1,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = _encode_token(payload)
    with pytest.raises(InvalidRefreshTokenException):
        await svc.refresh_access_token(token)


@patch("src.services.auth.settings")
async def test_refresh_wrong_type(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    svc = _make_service()
    payload = {
        "user_id": 1,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = _encode_token(payload)
    with pytest.raises(InvalidRefreshTokenException):
        await svc.refresh_access_token(token)


@patch("src.services.auth.settings")
async def test_refresh_blacklisted(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    bl = _make_blacklist(is_blacklisted_value=True)
    svc = _make_service(blacklist=bl)

    payload = {
        "user_id": 1,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    token = _encode_token(payload)
    with pytest.raises(InvalidRefreshTokenException):
        await svc.refresh_access_token(token)


@patch("src.services.auth.settings")
async def test_refresh_no_user_id(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    svc = _make_service()
    payload = {"type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=30)}
    token = _encode_token(payload)
    with pytest.raises(InvalidRefreshTokenException):
        await svc.refresh_access_token(token)


@patch("src.services.auth.settings")
async def test_refresh_user_deleted(mock_settings):
    mock_settings.JWT_SECRET_KEY = SECRET
    mock_settings.JWT_ALGORITHM = ALGORITHM
    mock_settings.JWT_SECRET_KEY_PREVIOUS = None

    db = _make_db()
    db.users.get_one_or_none.return_value = None
    svc = _make_service(db)

    payload = {
        "user_id": 999,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    token = _encode_token(payload)
    with pytest.raises(InvalidRefreshTokenException):
        await svc.refresh_access_token(token)


# ─── Update password ─────────────────────────────────────────────────────────


async def test_update_password_success():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("OldPass1xxx")
    mock_user = MagicMock(hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserPasswordUpdate

    await svc.update_password(
        1, UserPasswordUpdate(current_password="OldPass1xxx", new_password="NewPass1yyy")
    )
    db.users.update_hashed_password.assert_called_once()
    db.commit.assert_called_once()


async def test_update_password_wrong_current():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("CorrectPass1")
    mock_user = MagicMock(hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserPasswordUpdate

    with pytest.raises(IncorrectPasswordException):
        await svc.update_password(
            1, UserPasswordUpdate(current_password="WrongPass1x", new_password="NewPass1yyy")
        )


# ─── Update email ────────────────────────────────────────────────────────────


async def test_update_email_success():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("Password1xx")
    mock_user = MagicMock(email="old@example.com", hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user
    db.users.get_one_or_none.return_value = None  # new email is not taken

    from src.schemas.users import UserEmailUpdate

    await svc.update_email(
        1, UserEmailUpdate(new_email="new@example.com", current_password="Password1xx")
    )
    db.users.update_email.assert_called_once_with(1, "new@example.com")
    db.commit.assert_called_once()


async def test_update_email_same():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("Password1xx")
    mock_user = MagicMock(email="same@example.com", hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserEmailUpdate

    with pytest.raises(SameEmailException):
        await svc.update_email(
            1, UserEmailUpdate(new_email="same@example.com", current_password="Password1xx")
        )


async def test_update_email_wrong_password():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("CorrectPass1")
    mock_user = MagicMock(email="old@example.com", hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserEmailUpdate

    with pytest.raises(IncorrectPasswordException):
        await svc.update_email(
            1, UserEmailUpdate(new_email="new@example.com", current_password="WrongPass1x")
        )


async def test_update_email_already_taken():
    db = _make_db()
    svc = _make_service(db)
    old_hash = svc.hash_password("Password1xx")
    mock_user = MagicMock(email="old@example.com", hashed_password=old_hash)
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user
    db.users.update_email.side_effect = ObjectAlreadyExistsException()

    from src.schemas.users import UserEmailUpdate

    with pytest.raises(UserAlreadyExistsException):
        await svc.update_email(
            1, UserEmailUpdate(new_email="taken@example.com", current_password="Password1xx")
        )


# ─── get_one_or_none_user ────────────────────────────────────────────────────


async def test_get_one_or_none_user():
    db = _make_db()
    mock_user = MagicMock(id=1)
    db.users.get_one_or_none.return_value = mock_user
    svc = _make_service(db)

    result = await svc.get_one_or_none_user(1)
    assert result is mock_user


async def test_get_one_or_none_user_missing():
    db = _make_db()
    db.users.get_one_or_none.return_value = None
    svc = _make_service(db)

    result = await svc.get_one_or_none_user(999)
    assert result is None


# ─── OAuth guards ─────────────────────────────────────────────────────────────
# OAuth-only users have hashed_password=None — login and password update must
# reject them with IncorrectPasswordException (not AttributeError or crash).


async def test_login_oauth_user_raises_incorrect_password():
    """OAuth user (no hashed_password) cannot login with a password."""
    db = _make_db()
    svc = _make_service(db)
    mock_user = MagicMock(id=1, hashed_password=None, is_admin=False)
    db.users.get_user_with_hashed_password.return_value = mock_user

    from src.schemas.users import UserRequestAdd

    with pytest.raises(IncorrectPasswordException):
        await svc.login_user(UserRequestAdd(email="oauth@example.com", password="AnyPass1"))


async def test_update_password_oauth_user_raises_incorrect_password():
    """OAuth user (no hashed_password) cannot change password via PATCH."""
    db = _make_db()
    svc = _make_service(db)
    mock_user = MagicMock(id=1, hashed_password=None, email="oauth@example.com")
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserPasswordUpdate

    with pytest.raises(IncorrectPasswordException):
        await svc.update_password(
            1, UserPasswordUpdate(current_password="AnyPass1", new_password="NewPass2")
        )


async def test_update_email_oauth_user_raises_incorrect_password():
    """OAuth user (no hashed_password) cannot change email via PATCH."""
    db = _make_db()
    svc = _make_service(db)
    mock_user = MagicMock(id=1, hashed_password=None, email="oauth@example.com")
    db.users.get_user_with_hashed_password_by_id.return_value = mock_user

    from src.schemas.users import UserEmailUpdate

    with pytest.raises(IncorrectPasswordException):
        await svc.update_email(
            1, UserEmailUpdate(new_email="new@example.com", current_password="AnyPass1")
        )
