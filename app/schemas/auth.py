"""
Auth Pydantic schemas — request bodies and response shapes for signup/login.
"""

from pydantic import BaseModel, EmailStr, field_validator, Field


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address.", examples=["johndoe@example.com"])
    password: str = Field(..., description="A secure password. Must be at least 6 characters.", examples=["securepassword123"])
    full_name: str = Field(..., description="The user's full name.", examples=["John Doe"])

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's registered email address.", examples=["johndoe@example.com"])
    password: str = Field(..., description="The user's password.", examples=["securepassword123"])


class UserResponse(BaseModel):
    """Public user shape — never exposes hashed_password."""
    id: str
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
