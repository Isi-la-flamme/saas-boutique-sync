from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    tenant_id: UUID
    email: EmailStr
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="user", min_length=2, max_length=50)


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    username: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }