from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
import models, schemas


# ==========================================
# ITEMS
# ==========================================

def get_menu_items(db: Session):
    return db.query(models.Item).filter(models.Item.deleted_at == None).all()


def get_available_items(db: Session):
    return db.query(models.Item).filter(
        models.Item.available == True,
        models.Item.deleted_at == None,
    ).all()


def get_restock_list(db: Session):
    return db.query(models.Item).filter(
        models.Item.stock_quantity <= 0,
        models.Item.deleted_at == None,
    ).all()


def adjust_inventory(db: Session, item_id: int, new_quantity: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item and item.stock_quantity != new_quantity:
        item.stock_quantity = new_quantity
        item.modified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item


def decrease_inventory_after_order(db: Session, item_id: int, quantity_to_remove: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item and item.stock_quantity is not None:
        if item.stock_quantity >= quantity_to_remove:
            item.stock_quantity -= quantity_to_remove
            item.modified_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(item)
            return item
        else:
            return None
    return item


def decrease_option_stock(db: Session, item_option_id: int, quantity: int):
    option = db.query(models.ItemOption).filter(models.ItemOption.id == item_option_id).first()
    if option and option.stock_quantity >= quantity:
        option.stock_quantity -= quantity
        db.flush()
        return option
    return None


def restore_option_stock(db: Session, item_option_id: int, quantity: int):
    option = db.query(models.ItemOption).filter(models.ItemOption.id == item_option_id).first()
    if option:
        option.stock_quantity += quantity
        db.flush()


# ==========================================
# SOFT DELETE / RESTORE
# ==========================================

def soft_delete_category(db: Session, category_id: int):
    now = datetime.now(timezone.utc)
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat or cat.deleted_at is not None:
        return None
    cat.deleted_at = now
    for item in cat.items:
        if item.deleted_at is None:
            item.deleted_at = now
            for opt in item.options:
                if opt.deleted_at is None:
                    opt.deleted_at = now
    db.commit()
    db.refresh(cat)
    return cat


def restore_category(db: Session, category_id: int):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat or cat.deleted_at is None:
        return None
    cat.deleted_at = None
    db.commit()
    db.refresh(cat)
    return cat


def soft_delete_item(db: Session, item_id: int):
    now = datetime.now(timezone.utc)
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item or item.deleted_at is not None:
        return None
    item.deleted_at = now
    for opt in item.options:
        if opt.deleted_at is None:
            opt.deleted_at = now
    db.commit()
    db.refresh(item)
    return item


def restore_item(db: Session, item_id: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item or item.deleted_at is None:
        return None
    item.deleted_at = None
    db.commit()
    db.refresh(item)
    return item


def soft_delete_item_option(db: Session, option_id: int):
    opt = db.query(models.ItemOption).filter(models.ItemOption.id == option_id).first()
    if not opt or opt.deleted_at is not None:
        return None
    opt.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(opt)
    return opt


def restore_item_option(db: Session, option_id: int):
    opt = db.query(models.ItemOption).filter(models.ItemOption.id == option_id).first()
    if not opt or opt.deleted_at is None:
        return None
    opt.deleted_at = None
    db.commit()
    db.refresh(opt)
    return opt


# ==========================================
# CATEGORIES
# ==========================================

def get_all_categories(db: Session):
    return db.query(models.Category).filter(models.Category.deleted_at == None).all()


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
        if not db_item:
            return None
        if db_item.stock_quantity is not None and db_item.stock_quantity < item_data.quantity:
            return None
        if item_data.selected_options:
            for sel_opt in item_data.selected_options:
                option = db.query(models.ItemOption).filter(
                    models.ItemOption.id == sel_opt.item_option_id
                ).first()
                if not option or option.stock_quantity < sel_opt.quantity:
                    return None

    for item_data in order_data.items:
        decrease_inventory_after_order(db, item_data.item_id, item_data.quantity)
        if item_data.selected_options:
            for sel_opt in item_data.selected_options:
                decrease_option_stock(db, sel_opt.item_option_id, sel_opt.quantity)

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
            comment=item_data.comment,
            unit_price=db_item.price if db_item else Decimal("0.00"),
            item_name_snapshot=db_item.name if db_item else "",
        )

        if item_data.selected_options:
            for sel_opt in item_data.selected_options:
                option = db.query(models.ItemOption).filter(
                    models.ItemOption.id == sel_opt.item_option_id
                ).first()
                new_order_item.selected_options.append(
                    models.OrderItemOption(
                        item_option_id=sel_opt.item_option_id,
                        quantity=sel_opt.quantity,
                        option_name_snapshot=option.name if option else "",
                    )
                )

        new_order.items.append(new_order_item)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


def cancel_order(db: Session, order_id: int):
    order = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.items)
            .joinedload(models.OrderItem.selected_options)
        )
        .filter(models.Order.id == order_id)
        .first()
    )

    if not order or order.status == models.OrderStatus.CANCELLED:
        return None

    for order_item in order.items:
        db_item = db.query(models.Item).filter(models.Item.id == order_item.item_id).first()
        if db_item and db_item.stock_quantity is not None:
            db_item.stock_quantity += order_item.quantity
            db_item.modified_at = datetime.now(timezone.utc)
        for sel_opt in order_item.selected_options:
            restore_option_stock(db, sel_opt.item_option_id, sel_opt.quantity)

    order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)

    return order
