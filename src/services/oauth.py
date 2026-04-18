import logging
import secrets
import uuid

import httpx

from src.config import settings
from src.exceptions import (
    InvalidOAuthStateException,
    OAuthProviderNotConfiguredException,
    UnsupportedOAuthProviderException,
)
from src.schemas.users import User, UserOAuthAdd
from src.services.base import BaseService
from src.utils.db_manager import DBManager

logger = logging.getLogger(__name__)

OAUTH_STATE_TTL = 600  # 10 minutes
OAUTH_STATE_PREFIX = "oauth_state:"

_PROVIDER_CONFIG: dict[str, dict] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
}


def _get_client_credentials(provider: str) -> tuple[str, str]:
    """Возвращает (client_id, client_secret) для провайдера или выбрасывает исключение."""
    if provider == "google":
        cid, csecret = settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET
    else:
        raise UnsupportedOAuthProviderException()

    if not cid or not csecret:
        raise OAuthProviderNotConfiguredException()

    return cid, csecret


class OAuthService(BaseService):
    """Сервис для OAuth 2.0 Authorization Code Flow."""

    def __init__(self, db: DBManager | None = None, redis=None) -> None:
        super().__init__(db)
        self._redis = redis

    async def create_authorization_url(self, provider: str) -> str:
        """
        Генерирует URL для редиректа пользователя на страницу OAuth-провайдера.
        Сохраняет state в Redis для CSRF-защиты.
        """
        if provider not in _PROVIDER_CONFIG:
            raise UnsupportedOAuthProviderException()

        client_id, _ = _get_client_credentials(provider)
        cfg = _PROVIDER_CONFIG[provider]

        state = secrets.token_urlsafe(32)
        await self._redis.set(
            f"{OAUTH_STATE_PREFIX}{state}",
            provider,
            expire=OAUTH_STATE_TTL,
        )

        redirect_uri = f"{settings.APP_BASE_URL}/oauth/callback"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": cfg["scope"],
            "state": state,
        }
        if provider == "google":
            params["access_type"] = "online"

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{cfg['auth_url']}?{query}"

    async def handle_callback(self, provider: str, code: str, state: str) -> tuple[User, bool]:
        """
        Обрабатывает OAuth callback.
        Возвращает (user, is_new) — пользователя и флаг, был ли он только что создан.
        """
        if provider not in _PROVIDER_CONFIG:
            raise UnsupportedOAuthProviderException()

        # Verify state (CSRF protection)
        state_key = f"{OAUTH_STATE_PREFIX}{state}"
        stored = await self._redis.get(state_key)
        if not stored:
            raise InvalidOAuthStateException()
        if isinstance(stored, bytes):
            stored = stored.decode()
        if stored != provider:
            raise InvalidOAuthStateException()
        await self._redis.delete(state_key)

        _get_client_credentials(provider)  # validate configured
        client_id, client_secret = _get_client_credentials(provider)
        cfg = _PROVIDER_CONFIG[provider]
        redirect_uri = f"{settings.APP_BASE_URL}/oauth/callback"

        # Exchange code → access token
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                cfg["token_url"],
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()

            content_type = token_resp.headers.get("content-type", "")
            if "json" in content_type:
                token_data = token_resp.json()
            else:
                # GitHub returns form-encoded
                from urllib.parse import parse_qs

                parsed = parse_qs(token_resp.text)
                token_data = {k: v[0] for k, v in parsed.items()}

            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("OAuth token exchange failed: %s", token_data)
                raise OAuthProviderNotConfiguredException()

            # Fetch user info
            userinfo_resp = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

        # Normalize userinfo (Google)
        oauth_id = userinfo.get("sub") or str(userinfo.get("id", ""))
        email = (userinfo.get("email") or "").lower()
        name = userinfo.get("name") or userinfo.get("given_name") or ""
        avatar = userinfo.get("picture")

        if not oauth_id:
            raise OAuthProviderNotConfiguredException()

        # Look up existing OAuth user
        existing = await self.db.users.get_by_oauth(provider, oauth_id)
        if existing:
            return existing, False

        # If email is known, check for existing account — link OAuth if found
        if email:
            by_email = await self.db.users.get_one_or_none(email=email)
            if by_email is not None:
                if by_email.oauth_provider != provider:
                    await self.db.users.link_oauth(by_email.id, provider, oauth_id, avatar)
                    await self.db.commit()
                return by_email, False

        # Create new user
        first_name = name.split()[0] if name else None
        user_data = UserOAuthAdd(
            email=email or f"oauth_{provider}_{uuid.uuid4().hex}@noreply",
            oauth_provider=provider,
            oauth_id=oauth_id,
            oauth_avatar_url=avatar,
            first_name=first_name,
        )
        new_user = await self.db.users.create_oauth_user(user_data)
        await self.db.commit()
        return new_user, True
