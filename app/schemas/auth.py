from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str | None = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)
    full_name: str | None = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None

    class Config:
        from_attributes = True
