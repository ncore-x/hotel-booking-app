from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, computed_field, field_validator

from src.validators import validate_email_russian, validate_password_russian


class UserRequestAdd(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def normalize_email(cls, email: str) -> str:
        return email.lower()

    _validate_email = field_validator("email")(validate_email_russian)
    _validate_password = field_validator("password")(validate_password_russian)


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

    _validate_new_password = field_validator("new_password")(validate_password_russian)


class UserEmailUpdate(BaseModel):
    new_email: str
    current_password: str

    @field_validator("new_email")
    def normalize_email(cls, v: str) -> str:
        return v.lower()

    _validate_email = field_validator("new_email")(validate_email_russian)


class UserAdd(BaseModel):
    email: EmailStr
    hashed_password: str | None = None


class UserOAuthAdd(BaseModel):
    email: str
    oauth_provider: str
    oauth_id: str
    oauth_avatar_url: str | None = None
    first_name: str | None = None


class UserProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    citizenship: str | None = None


class User(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool = False
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    citizenship: str | None = None
    avatar_filename: str | None = None
    oauth_provider: str | None = None
    oauth_avatar_url: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avatar_url(self) -> str | None:
        if self.avatar_filename:
            return f"/static/images/{self.avatar_filename}"
        if self.oauth_avatar_url:
            return self.oauth_avatar_url
        return None

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
