from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from src.validators import validate_email_russian, validate_password_russian


class UserRequestAdd(BaseModel):
    email: str
    password: str


class UserRequestAdd(BaseModel):
    email: str
    password: str

    # Валидация email и password с русскими сообщениями
    _validate_email = field_validator("email")(validate_email_russian)
    _validate_password = field_validator("password")(validate_password_russian)


class UserAdd(BaseModel):
    email: EmailStr
    hashed_password: str


class User(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str
