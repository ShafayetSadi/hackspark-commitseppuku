from pydantic import AliasChoices, BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("name", "full_name"),
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    @classmethod
    def from_model(cls, user) -> "UserResponse":
        return cls(id=user.id, email=user.email, name=user.full_name)
