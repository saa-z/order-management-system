from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from models import OrderStatus, OrderType, SeatingLocation, UserRole


# ==========================================
# 0. USERS & AUTH
# ==========================================

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.SERVER


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    active: Optional[bool] = None  # False = révoqué (soft-delete), True = réactivé


class UserRead(BaseModel):
    id: int
    username: str
    password: Optional[str] = None  # visible : l'admin gère les mdp en clair
    role: UserRole
    active: bool = True
    created_at: datetime
    deleted_at: Optional[datetime] = None  # date de révocation
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ==========================================
# 0b. INGREDIENTS
# ==========================================

class IngredientCreate(BaseModel):
    name: str
    is_base: bool = False


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    is_base: Optional[bool] = None


class IngredientRead(BaseModel):
    id: int
    name: str
    is_base: bool = False
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 0c. ORDER ITEM MODIFICATIONS
# ==========================================

class OrderItemModificationCreate(BaseModel):
    ingredient_id: int
    modification_type: str  # "remove", "add", "base_change"


class OrderItemModificationRead(BaseModel):
    id: int
    ingredient_id: int
    modification_type: str
    unit_price: Decimal
    ingredient_name_snapshot: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


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
    category_name: Optional[str] = None
    options: List[ItemOptionRead] = []
    ingredients: List[IngredientRead] = []
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
    modifications: Optional[List[OrderItemModificationCreate]] = None


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
    batch: int = 1
    item: ItemRead
    selected_options: List[OrderItemOptionRead] = []
    modifications: List[OrderItemModificationRead] = []

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
    created_by: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


OrderRead.model_rebuild()
OrderItemRead.model_rebuild()


# ==========================================
# 7. PRINT JOBS (file d'impression centralisée)
# ==========================================

class PrintJobRead(BaseModel):
    id: int
    order_id: int
    job_type: str
    batch: Optional[int] = None
    status: str
    created_at: datetime
    printed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
