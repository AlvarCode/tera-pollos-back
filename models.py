from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    user_id: int
    password: str


class User(BaseModel):
    id: int
    name: str
    is_admin: Optional[bool] = False


class Product(BaseModel):
    name: str
    price: float


class Combo(BaseModel):
    name: str
    price: float
    products: Optional[list[dict]] = None


class Sale(BaseModel):
    id: Optional[int]
    date: Optional[datetime] = datetime.now()
    total: float
    seller_id: int


class SaleDetail(Sale):
    products: Optional[list[dict]] = None
    combos: Optional[list[dict]] = None