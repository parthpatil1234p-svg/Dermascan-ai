from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.user import ALLOWED_AGE_GROUPS, UserPublic


def clean_text(value: str) -> str:
    return " ".join(value.strip().split())


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    age_group: str | None = None
    location: str | None = Field(default=None, max_length=120)
    accept_terms: bool

    @field_validator("full_name", "location", mode="before")
    @classmethod
    def sanitize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(str(value))

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("age_group", mode="before")
    @classmethod
    def sanitize_age_group(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(str(value))

    @model_validator(mode="after")
    def validate_registration(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")

        if not self.accept_terms:
            raise ValueError("Terms and privacy agreement must be accepted.")

        if self.age_group and self.age_group not in ALLOWED_AGE_GROUPS:
            raise ValueError("Age group is not supported.")

        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return str(value).strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class LogoutResponse(BaseModel):
    message: str
