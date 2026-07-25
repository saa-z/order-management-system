from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Union

from models import OrderStatus, OrderType, SeatingLocation


# ==========================================
# 1. ITEMS
# ==========================================

class ItemBase(BaseModel):
    name: str
    price: Decimal
    available: bool = True
    stock_quantity: Optional[int] = None
    category_id: int
    options: Optional[Union[List[str], Dict[str, int]]] = None
    last_modified: Optional[datetime] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    available: Optional[bool] = None
    stock_quantity: Optional[int] = None
    options: Optional[Union[List[str], Dict[str, int]]] = None
    category_id: Optional[int] = None
    last_modified: Optional[datetime] = None


class ItemRead(ItemBase):
    id: int
    is_in_stock: bool = True
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. ORDER ITEMS
# ==========================================

class OrderItemBase(BaseModel):
    item_id: int
    quantity: int = 1
    comment: Optional[str] = None
    selected_options: Optional[Dict[str, int]] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: int
    order_id: int
    unit_price: Decimal = Decimal("0.00")
    item: ItemRead

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. CATEGORIES
# ==========================================

class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int
    available: bool = False
    model_config = ConfigDict(from_attributes=True)


class CategoryWithItems(CategoryRead):
    items: List[ItemRead] = []


# ==========================================
# 4. ORDERS
# ==========================================

class OrderBase(BaseModel):
    table_number: Optional[int] = None
    covers: Optional[int] = None
    seating_location: Optional[SeatingLocation] = None
    order_type: OrderType = OrderType.EAT_IN
    pickup_time: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderUpdateItems(BaseModel):
    items: List[OrderItemCreate]


class OrderRead(OrderBase):
    id: int
    status: OrderStatus
    total_price: Decimal = Decimal("0.00")
    created_at: datetime
    validated_at: Optional[datetime] = None
    pickup_time: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)


OrderRead.model_rebuild()
OrderItemRead.model_rebuild()
