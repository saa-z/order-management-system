from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session, joinedload
import models, schemas
# ==========================================
# USERS
# ==========================================

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(
        models.User.username == username,
        models.User.deleted_at == None,
    ).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)  # exclut déjà les révoqués (deleted_at)
    if not user:
        return None
    if user.password != password:  # comparaison en clair (choix assumé)
        return None
    return user


def create_user(db: Session, data: schemas.UserCreate) -> Optional[models.User]:
    if get_user_by_username(db, data.username):
        return None
    user = models.User(username=data.username, password=data.password, role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: schemas.UserUpdate) -> Optional[models.User]:
    from datetime import datetime, timezone
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    if data.username is not None:
        existing = db.query(models.User).filter(
            models.User.username == data.username,
            models.User.id != user_id,
            models.User.deleted_at == None,
        ).first()
        if existing:
            return None
        user.username = data.username
    if data.password is not None:
        user.password = data.password
    if data.role is not None:
        user.role = data.role
    if data.active is not None:
        # Révocation = soft-delete (on garde l'historique des commandes du user).
        user.deleted_at = None if data.active else datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, include_revoked: bool = False) -> list[models.User]:
    query = db.query(models.User)
    if not include_revoked:
        query = query.filter(models.User.deleted_at == None)
    return query.order_by(models.User.username).all()


def delete_user(db: Session, user_id: int) -> bool:
    """Révocation = soft-delete (conserve l'historique des commandes)."""
    from datetime import datetime, timezone
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.deleted_at == None,
    ).first()
    if not user:
        return False
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


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
    if not option:
        return None
    if option.stock_quantity is None:
        return option  # unlimited
    if option.stock_quantity >= quantity:
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
    # Restauration en cascade : on ne remonte que les enfants supprimés au même
    # instant que la catégorie (donc dans la même cascade de suppression).
    # Les enfants supprimés indépendamment avant gardent leur deleted_at.
    ts = cat.deleted_at
    cat.deleted_at = None
    for item in cat.items:
        if item.deleted_at == ts:
            item.deleted_at = None
            for opt in item.options:
                if opt.deleted_at == ts:
                    opt.deleted_at = None
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
    # Restaure aussi les options supprimées dans la même cascade (même timestamp).
    ts = item.deleted_at
    item.deleted_at = None
    for opt in item.options:
        if opt.deleted_at == ts:
            opt.deleted_at = None
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
        if item_data.modifications:
            for mod in item_data.modifications:
                if mod.modification_type == "add":
                    total += Decimal("1.00") * item_data.quantity
    return total


def place_order(db: Session, order_data: schemas.OrderCreate, user_id: Optional[int] = None):
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
                if not option or (option.stock_quantity is not None and option.stock_quantity < sel_opt.quantity):
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
        created_by_user_id=user_id,
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

        if item_data.modifications:
            for mod in item_data.modifications:
                ingredient = db.query(models.Ingredient).filter(
                    models.Ingredient.id == mod.ingredient_id
                ).first()
                price = Decimal("1.00") if mod.modification_type == "add" else Decimal("0.00")
                new_order_item.modifications.append(
                    models.OrderItemModification(
                        ingredient_id=mod.ingredient_id,
                        modification_type=mod.modification_type,
                        unit_price=price,
                        ingredient_name_snapshot=ingredient.name if ingredient else None,
                    )
                )

        new_order.items.append(new_order_item)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


def add_items_to_order(db: Session, order_id: int, items_data: list[schemas.OrderItemCreate]):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order or order.status in [models.OrderStatus.PAID, models.OrderStatus.CANCELLED]:
        return None

    max_batch = db.query(sqlfunc.max(models.OrderItem.batch)).filter(
        models.OrderItem.order_id == order_id
    ).scalar() or 0
    next_batch = max_batch + 1

    for item_data in items_data:
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
                if not option or (option.stock_quantity is not None and option.stock_quantity < sel_opt.quantity):
                    return None

    added_total = Decimal("0.00")
    for item_data in items_data:
        db_item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        decrease_inventory_after_order(db, item_data.item_id, item_data.quantity)

        new_item = models.OrderItem(
            order_id=order_id,
            item_id=item_data.item_id,
            quantity=item_data.quantity,
            comment=item_data.comment,
            unit_price=db_item.price if db_item else Decimal("0.00"),
            item_name_snapshot=db_item.name if db_item else "",
            batch=next_batch,
        )
        if item_data.selected_options:
            for sel_opt in item_data.selected_options:
                option = db.query(models.ItemOption).filter(
                    models.ItemOption.id == sel_opt.item_option_id
                ).first()
                decrease_option_stock(db, sel_opt.item_option_id, sel_opt.quantity)
                new_item.selected_options.append(models.OrderItemOption(
                    item_option_id=sel_opt.item_option_id,
                    quantity=sel_opt.quantity,
                    option_name_snapshot=option.name if option else "",
                ))

        if item_data.modifications:
            for mod in item_data.modifications:
                ingredient = db.query(models.Ingredient).filter(
                    models.Ingredient.id == mod.ingredient_id
                ).first()
                price = Decimal("1.00") if mod.modification_type == "add" else Decimal("0.00")
                new_item.modifications.append(models.OrderItemModification(
                    ingredient_id=mod.ingredient_id,
                    modification_type=mod.modification_type,
                    unit_price=price,
                    ingredient_name_snapshot=ingredient.name if ingredient else None,
                ))
                if mod.modification_type == "add":
                    added_total += Decimal("1.00") * item_data.quantity

        added_total += (db_item.price if db_item else Decimal("0.00")) * item_data.quantity
        db.add(new_item)

    order.total_price += added_total
    db.commit()
    db.refresh(order)
    return order


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
