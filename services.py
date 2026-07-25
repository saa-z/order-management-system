from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
import models, schemas


# ==========================================
# ITEMS
# ==========================================

def get_menu_items(db: Session):
    return db.query(models.Item).all()


def get_available_items(db: Session):
    return db.query(models.Item).filter(models.Item.available == True).all()


def get_restock_list(db: Session):
    return db.query(models.Item).filter(models.Item.stock_quantity <= 0).all()


def adjust_inventory(db: Session, item_id: int, new_quantity: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item and item.stock_quantity != new_quantity:
        item.stock_quantity = new_quantity
        item.last_modified = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item


def decrease_inventory_after_order(db: Session, item_id: int, quantity_to_remove: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if item and item.stock_quantity is not None:
        if item.stock_quantity >= quantity_to_remove:
            item.stock_quantity -= quantity_to_remove
            item.last_modified = datetime.now(timezone.utc)
            db.commit()
            db.refresh(item)
            return item
        else:
            return None
    return item


# ==========================================
# CATEGORIES
# ==========================================

def get_all_categories(db: Session):
    return db.query(models.Category).all()


# ==========================================
# ORDERS
# ==========================================

def calculate_order_total(db: Session, order_items: list[schemas.OrderItemCreate]) -> Decimal:
    total = Decimal("0.00")
    for item_data in order_items:
        db_item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        if db_item:
            total += db_item.price * item_data.quantity
    return total


def place_order(db: Session, order_data: schemas.OrderCreate):
    for item_data in order_data.items:
        db_item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        if not db_item or (db_item.stock_quantity is not None and db_item.stock_quantity < item_data.quantity):
            return None

    for item_data in order_data.items:
        decrease_inventory_after_order(db, item_data.item_id, item_data.quantity)

    total = calculate_order_total(db, order_data.items)

    new_order = models.Order(
        table_number=order_data.table_number,
        covers=order_data.covers,
        seating_location=order_data.seating_location,
        order_type=order_data.order_type,
        pickup_time=order_data.pickup_time,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        status=models.OrderStatus.PENDING,
        total_price=total,
    )

    for item_data in order_data.items:
        db_item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        new_order_item = models.OrderItem(
            item_id=item_data.item_id,
            quantity=item_data.quantity,
            selected_options=item_data.selected_options,
            comment=item_data.comment,
            unit_price=db_item.price if db_item else Decimal("0.00"),
        )
        new_order.items.append(new_order_item)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


def cancel_order(db: Session, order_id: int):
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.id == order_id)
        .first()
    )

    if not order or order.status == models.OrderStatus.CANCELLED:
        return None

    for order_item in order.items:
        db_item = db.query(models.Item).filter(models.Item.id == order_item.item_id).first()

        if db_item and db_item.stock_quantity is not None:
            db_item.stock_quantity += order_item.quantity
            db_item.last_modified = datetime.now(timezone.utc)

    order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)

    return order
