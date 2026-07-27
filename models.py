from decimal import Decimal
from enum import StrEnum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey, func
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
    name: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    modified_at: Mapped[Optional[datetime]] = mapped_column(default=None, onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    items: Mapped[list["Item"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    @property
    def available(self) -> bool:
        return any(
            item.is_in_stock for item in self.items
            if item.deleted_at is None
        )


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    price: Mapped[Decimal] = mapped_column()
    available: Mapped[bool] = mapped_column(default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    modified_at: Mapped[Optional[datetime]] = mapped_column(default=None, onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    category: Mapped["Category"] = relationship(back_populates="items")

    options: Mapped[list["ItemOption"]] = relationship(back_populates="item", cascade="all, delete-orphan")

    @property
    def is_in_stock(self) -> bool:
        if self.deleted_at is not None:
            return False
        if not self.available:
            return False
        if self.stock_quantity is not None:
            return self.stock_quantity > 0
        active_options = [o for o in self.options if o.deleted_at is None]
        if active_options:
            return any(opt.stock_quantity is None or opt.stock_quantity > 0 for opt in active_options)
        return True


class ItemOption(Base):
    __tablename__ = "item_options"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String)
    stock_quantity: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    modified_at: Mapped[Optional[datetime]] = mapped_column(default=None, onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    item: Mapped["Item"] = relationship(back_populates="options")


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
    quantity: Mapped[int] = mapped_column(default=1)
    comment: Mapped[Optional[str]] = mapped_column(String, default=None)
    unit_price: Mapped[Decimal] = mapped_column(default=Decimal("0.00"))
    item_name_snapshot: Mapped[Optional[str]] = mapped_column(String, default=None)

    order: Mapped["Order"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship()
    selected_options: Mapped[list["OrderItemOption"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )


class OrderItemOption(Base):
    __tablename__ = "order_item_options"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"))
    item_option_id: Mapped[int] = mapped_column(ForeignKey("item_options.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(default=1)
    option_name_snapshot: Mapped[Optional[str]] = mapped_column(String, default=None)

    order_item: Mapped["OrderItem"] = relationship(back_populates="selected_options")
    option: Mapped["ItemOption"] = relationship()
