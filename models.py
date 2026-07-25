from decimal import Decimal
from enum import StrEnum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class OrderType(StrEnum):
    EAT_IN = "eat_in"
    TAKE_AWAY = "take_away"


class SeatingLocation(StrEnum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class OrderStatus(StrEnum):
    PENDING = "pending"
    IN_KITCHEN = "in_kitchen"
    READY = "ready"
    PAID = "paid"
    CANCELLED = "cancelled"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    items: Mapped[list["Item"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    @property
    def available(self) -> bool:
        return any(item.is_in_stock for item in self.items)


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("name", "category_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    price: Mapped[Decimal] = mapped_column()
    available: Mapped[bool] = mapped_column(default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(default=None)
    options: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    last_modified: Mapped[Optional[datetime]] = mapped_column(default=None, onupdate=func.now())

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    category: Mapped["Category"] = relationship(back_populates="items")

    @property
    def is_in_stock(self) -> bool:
        if not self.available:
            return False
        if self.stock_quantity is not None:
            return self.stock_quantity > 0
        if self.options and isinstance(self.options, dict):
            return any(qty > 0 for qty in self.options.values())
        return True


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    table_number: Mapped[Optional[int]] = mapped_column(default=None)
    covers: Mapped[Optional[int]] = mapped_column(default=None)
    seating_location: Mapped[Optional["SeatingLocation"]] = mapped_column(default=None)
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING, index=True)
    total_price: Mapped[Decimal] = mapped_column(default=Decimal("0.00"))
    order_type: Mapped[OrderType] = mapped_column(default=OrderType.EAT_IN)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    pickup_time: Mapped[Optional[str]] = mapped_column(String, default=None)
    customer_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    customer_phone: Mapped[Optional[str]] = mapped_column(String, default=None)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"))
    selected_options: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    quantity: Mapped[int] = mapped_column(default=1)
    comment: Mapped[Optional[str]] = mapped_column(String, default=None)
    unit_price: Mapped[Decimal] = mapped_column(default=Decimal("0.00"))

    order: Mapped["Order"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship()
