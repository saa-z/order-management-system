# operations.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
import models, schemas

# ==========================================
# ITEMS
# ==========================================

def get_menu_items(db: Session):
    """Retrieve all menu items."""
    return db.query(models.Item).all()

def get_available_items(db: Session):
    """Retrieve only items currently available for sale."""
    return db.query(models.Item).filter(models.Item.disponible == True).all()

def get_restock_list(db: Session):
    """Retrieve items that are out of stock (quantity <= 0)."""
    return db.query(models.Item).filter(models.Item.quantite_en_stock <= 0).all()

def adjust_inventory(db: Session, item_id: int, new_quantity: int):
    """Update stock, timestamp, and availability status."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item and item.quantite_en_stock != new_quantity:
        item.quantite_en_stock = new_quantity
        item.last_modified = datetime.now(timezone.utc)
        item.disponible = new_quantity > 0
        db.commit()
        db.refresh(item)
    return item

def decrease_inventory_after_order(db: Session, item_id: int, quantity_to_remove: int):
    """
    Subtracts quantity from stock, updates timestamp and availability.
    """
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    # Verify if the item exists and is tracking stock
    if item and item.quantite_en_stock is not None:
        # Check if enough stock exists to fulfill the request
        if item.quantite_en_stock >= quantity_to_remove:
            # Subtract the ordered quantity from current stock
            item.quantite_en_stock -= quantity_to_remove
            # Update the last_modified timestamp only when a change occurs
            item.last_modified = datetime.now(timezone.utc)
            # Update availability status (True if stock > 0, otherwise False)
            item.disponible = item.quantite_en_stock > 0

            db.commit()
            db.refresh(item)

            # Refresh category availability status
            refresh_category_availability(db, item.categorie_id)
            return item
        else:
            # Stock insufficient: return None to trigger an error in the route
            return None
    return item

# ==========================================
# CATEGORIES
# ==========================================

def get_all_categories(db: Session):
    """Retrieve all categories with their associated items."""
    return db.query(models.Categorie).all()

def refresh_category_availability(db: Session, categorie_id: int):
    """
    Checks if at least one item in the category is available.
    If no items are available, sets the category to unavailable (disponible=False).
    """
    has_available_items = db.query(models.Item).filter(
        models.Item.categorie_id == categorie_id,
        models.Item.disponible == True
    ).first() is not None

    category = db.query(models.Categorie).filter(models.Categorie.id == categorie_id).first()
    if category:
        category.disponible = has_available_items
        db.commit()

# ==========================================
# ORDERS
# ==========================================
def place_order(db: Session, order_data: schemas.CommandeCreate):
    # 1. Check stock for all items
    for item_data in order_data.items:
        db_item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        if not db_item or (db_item.quantite_en_stock is not None and db_item.quantite_en_stock < item_data.quantite):
            return None

    # 2. Decrement stock
    for item_data in order_data.items:
        decrease_inventory_after_order(db, item_data.item_id, item_data.quantite)

    # 3. Create the order
    new_order = models.Commande(table=order_data.table, statut="en_attente")

    for item_data in order_data.items:
        new_order_item = models.CommandeItem(
            item_id=item_data.item_id,
            quantite=item_data.quantite
        )
        new_order.items.append(new_order_item)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

def cancel_order(db: Session, order_id: int):
    # Retrieve the order with its items
    order = (
        db.query(models.Commande)
        .options(joinedload(models.Commande.items))
        .filter(models.Commande.id == order_id)
        .first()
    )

    if not order or order.statut == "annulee":
        return None

    # Restore stock
    for order_item in order.items:
        db_item = db.query(models.Item).filter(models.Item.id == order_item.item_id).first()

        if db_item and db_item.quantite_en_stock is not None:
            db_item.quantite_en_stock += order_item.quantite
            db_item.last_modified = datetime.now(timezone.utc)
            db_item.disponible = True

            # Update category availability if needed
            refresh_category_availability(db, db_item.categorie_id)

    # Finalize cancellation
    order.statut = "annulee"
    db.commit()
    db.refresh(order)

    return order