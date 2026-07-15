from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import get_db
import services

# Define router with its prefix and documentation tag
router = APIRouter(
    prefix="/commandes",
    tags=["Commandes"]
)


@router.post("/", response_model=schemas.Commande, status_code=status.HTTP_201_CREATED)
def create_order(commande: schemas.CommandeCreate, db: Session = Depends(get_db)):
    """
    Create a new order for a table with its initial items.
    """
    # 1. Create the main Order entry
    db_commande = models.Commande(table=commande.table)
    db.add(db_commande)
    db.commit()  # Committed to generate the order ID
    db.refresh(db_commande)

    # 2. Add each item to the order
    try:
        for item_data in commande.items:
            # Verify that the item exists and is available
            item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
            if not item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item with ID {item_data.item_id} not found."
                )
            if not item.disponible:
                raise HTTPException(
                    status_code=400,
                    detail=f"Item '{item.nom}' is currently out of stock."
                )

            db_order_item = models.CommandeItem(
                commande_id=db_commande.id,
                item_id=item_data.item_id,
                quantite=item_data.quantite,
                commentaire=item_data.commentaire
            )
            db.add(db_order_item)

        db.commit()
    except Exception as e:
        db.rollback()
        # Clean up: delete the empty order shell if item insertion fails
        db.delete(db_commande)
        db.commit()
        raise e

    db.refresh(db_commande)
    return db_commande


@router.get("/", response_model=List[schemas.Commande])
def list_orders(statut: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retrieve all orders. Can be filtered by status (e.g. ?statut=en_cuisine).
    Orders are returned from newest to oldest.
    """
    query = db.query(models.Commande)
    if statut:
        query = query.filter(models.Commande.statut == statut)
    return query.order_by(models.Commande.date_creation.desc()).all()


@router.get("/{commande_id}", response_model=schemas.Commande)
def get_order(commande_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific order's details.
    """
    db_commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not db_commande:
        raise HTTPException(status_code=404, detail="Order not found.")
    return db_commande


@router.put("/{commande_id}/statut", response_model=schemas.Commande)
def update_order_status(commande_id: int, status_update: schemas.CommandeUpdateStatus, db: Session = Depends(get_db)):
    """
    Update the status of an order (e.g., transition to 'en_cuisine', 'pret', or 'payee').
    """
    db_commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not db_commande:
        raise HTTPException(status_code=404, detail="Order not found.")

    valid_statuses = ["en_attente", "en_cuisine", "pret", "payee"]
    if status_update.statut not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    db_commande.statut = status_update.statut
    db.commit()
    db.refresh(db_commande)
    return db_commande


@router.put("/{commande_id}/items", response_model=schemas.Commande)
def update_order_items(commande_id: int, items_update: schemas.CommandeUpdateItems, db: Session = Depends(get_db)):
    """
    Modify items inside an existing order (adding drinks/desserts, changing quantities, or deleting items).
    This safely replaces the entire item list of the order within a transaction.
    """
    db_commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not db_commande:
        raise HTTPException(status_code=404, detail="Order not found.")

    # 1. Clear all existing items from this order
    db.query(models.CommandeItem).filter(models.CommandeItem.commande_id == commande_id).delete()

    # 2. Insert the updated list of items
    for item_data in items_update.items:
        item = db.query(models.Item).filter(models.Item.id == item_data.item_id).first()
        if not item:
            db.rollback()
            raise HTTPException(
                status_code=404,
                detail=f"Item with ID {item_data.item_id} not found."
            )

        db_order_item = models.CommandeItem(
            commande_id=commande_id,
            item_id=item_data.item_id,
            quantite=item_data.quantite,
            commentaire=item_data.commentaire
        )
        db.add(db_order_item)

    db.commit()
    db.refresh(db_commande)
    return db_commande


@router.delete("/{commande_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(commande_id: int, db: Session = Depends(get_db)):
    """
    Cancel and permanently delete an order from the database.
    """
    db_commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not db_commande:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Cascade delete will automatically clean 'commande_items' table
    db.delete(db_commande)
    db.commit()
    return None