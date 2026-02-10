from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


# ユーザー 
class UserCreate(BaseModel):
    """ユーザー作成時に受け取るデータ"""
    name: str
    role: str = "student"


class UserResponse(BaseModel):
    """ユーザー情報を返すときのデータ"""
    id: int
    name: str
    role: str
    created_at: str


# 本 
class BookCreate(BaseModel):
    """本を手動登録するときに受け取るデータ"""
    title: str
    description: str = ""
    cover_url: str = ""
    owner_id: Optional[int] = None


class BookISBNCreate(BaseModel):
    """ISBNで本を登録するときに受け取るデータ"""
    isbn: str
    owner_id: Optional[int] = None


class BookResponse(BaseModel):
    """本の情報を返すときのデータ"""
    id: int
    isbn: Optional[str]
    title: str
    description: str
    cover_url: str
    owner_id: Optional[int]
    owner_name: Optional[str] = None
    is_available: bool = True
    created_at: str


# 貸し出し
class LendingCreate(BaseModel):
    """貸し出し時に受け取るデータ"""
    borrower_id: int
    due_date: date


class LendingResponse(BaseModel):
    """貸し出し情報を返すときのデータ"""
    id: int
    book_id: int
    borrower_id: int
    borrower_name: Optional[str] = None
    borrowed_at: str
    due_date: str
    returned_at: Optional[str] = None