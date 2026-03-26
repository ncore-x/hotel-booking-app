from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

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


class UserAdd(BaseModel):
    email: EmailStr
    hashed_password: str


class User(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
