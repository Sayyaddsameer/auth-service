from pydantic import BaseModel, EmailStr
import uuid

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    accessToken: str
    refreshToken: str

class RefreshTokenRequest(BaseModel):
    refreshToken: str

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: str