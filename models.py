from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    products: Optional[list[Product]] = None


class Sale(BaseModel):
    id: int
    date: datetime
    products: Optional[list[tuple[Product, int]]] = None
    combos: Optional[list[tuple[Combo, int]]] = None
    total: float
    seller_id: int
