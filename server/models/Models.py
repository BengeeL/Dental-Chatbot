from uuid import UUID
from fastapi import UploadFile, File
from pydantic import BaseModel, EmailStr, Field, HttpUrl, Json
from typing import Optional, List
import re
import phonenumbers


class RefreshRequest(BaseModel):
    refresh_token: str


class ResendOTPRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UpdatePasswordRequest(BaseModel):
    access_token: str
    refresh_token: str
    new_password: str = Field(..., min_length=8, max_length=64)


class AuthUser(BaseModel):
    id: UUID = None
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    firstname: str = None
    lastname: str = None
    role: Optional[str] = ""

    @classmethod
    def validate_password(cls, password: str):
        """Validates password strength (at least 8 chars, 1 uppercase, 1 digit, 1 special char)"""
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            raise ValueError("Password must be at least 8 characters long, contain 1 uppercase letter, 1 number, and 1 special character")
        return password


class User(BaseModel):
    id: UUID = None
    email: Optional[EmailStr] = None
    role: Optional[str] = ""
    firstname: str = None
    lastname: str = None
