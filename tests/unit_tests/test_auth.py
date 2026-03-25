import time

import jwt
import pytest

from src.config import settings
from src.exceptions import ExpiredTokenException, IncorrectTokenException
from src.services.auth import AuthService


def test_create_access_token():
    data = {"user_id": 1}
    jwt_token = AuthService().create_access_token(data)

    assert jwt_token
    assert isinstance(jwt_token, str)


def test_decode_valid_token():
    svc = AuthService()
    token = svc.create_access_token({"user_id": 42})
    payload = svc.decode_token(token)
    assert payload["user_id"] == 42


def test_decode_invalid_token_raises():
    with pytest.raises(IncorrectTokenException):
        AuthService().decode_token("this.is.not.a.token")


def test_decode_expired_token_raises():
    expired = jwt.encode(
        {"user_id": 1, "exp": int(time.time()) - 1},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(ExpiredTokenException):
        AuthService().decode_token(expired)


def test_hash_and_verify_password():
    svc = AuthService()
    hashed = svc.hash_password("MySecret1")
    assert svc.verify_password("MySecret1", hashed)
    assert not svc.verify_password("WrongPass1", hashed)
