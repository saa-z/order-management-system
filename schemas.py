from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from models import OrderStatus, OrderType, SeatingLocation


# ==========================================
# 1. ITEM OPTIONS
# ==========================================

class ItemOptionBase(BaseModel):
    name: str
    stock_quantity: Optional[int] = None


class ItemOptionCreate(ItemOptionBase):
    pass


class ItemOptionUpdate(BaseModel):
    name: Optional[str] = None
    stock_quantity: Optional[int] = None


class ItemOptionRead(ItemOptionBase):
    id: int
    item_id: int
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. ITEMS
# ==========================================

class ItemBase(BaseModel):
    name: str
    price: Decimal
    available: bool = True
    stock_quantity: Optional[int] = None
    category_id: int


class ItemCreate(ItemBase):
    options: Optional[List[ItemOptionCreate]] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    available: Optional[bool] = None
    stock_quantity: Optional[int] = None
    category_id: Optional[int] = None


class ItemRead(ItemBase):
    id: int
    is_in_stock: bool = True
    options: List[ItemOptionRead] = []
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. ORDER ITEM OPTIONS
# ==========================================

class OrderItemOptionBase(BaseModel):
    item_option_id: int
    quantity: int = 1


class OrderItemOptionCreate(OrderItemOptionBase):
    pass


class OrderItemOptionRead(OrderItemOptionBase):
    id: int
    order_item_id: int
    option_name_snapshot: Optional[str] = None
    option: ItemOptionRead

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. ORDER ITEMS
# ==========================================

class OrderItemBase(BaseModel):
    item_id: int
    quantity: int = 1
    comment: Optional[str] = None
    selected_options: Optional[List[OrderItemOptionCreate]] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(BaseModel):
    id: int
    order_id: int
    item_id: int
    quantity: int = 1
    comment: Optional[str] = None
    unit_price: Decimal = Decimal("0.00")
    item_name_snapshot: Optional[str] = None
    item: ItemRead
    selected_options: List[OrderItemOptionRead] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. CATEGORIES
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
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CategoryWithItems(CategoryRead):
    items: List[ItemRead] = []


# ==========================================
# 6. ORDERS
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
    items: List[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)


OrderRead.model_rebuild()
OrderItemRead.model_rebuild()
