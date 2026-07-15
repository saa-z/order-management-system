from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
import services

# Configuration of items routes
router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

@router.post("/", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """
    Create an item and associate it with an existing category.
    """
    # Verify that the targeted category actually exists
    category = db.query(models.Categorie).filter(models.Categorie.id == item.categorie_id).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Associated category not found. Please create it first."
        )

    # Create the item with the new stock quantity
    new_item = models.Item(
        nom=item.nom,
        prix=item.prix,
        disponible=item.disponible,
        categorie_id=item.categorie_id,
        quantite_en_stock=item.quantite_en_stock
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item_to_update: schemas.ItemUpdate, db: Session = Depends(get_db)):
    """
    Update an existing item's information (name, price, category, availability, or stock).
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")

    # 1. Security check: prevent negative stock
    if item_to_update.quantite_en_stock is not None and item_to_update.quantite_en_stock < 0:
        raise HTTPException(
            status_code=400,
            detail="The stock quantity cannot be negative."
        )

    # 2. Verify existence of the new category if it is being changed
    if item_to_update.categorie_id is not None:
        category = db.query(models.Categorie).filter(models.Categorie.id == item_to_update.categorie_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="The specified new category does not exist.")

    # 3. Dynamically apply updates
    update_data = item_to_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[schemas.Item])
def list_items(db: Session = Depends(get_db)):
    """
    Retrieve all items from the database.
    """
    return db.query(models.Item).all()


@router.get("/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific item by its ID.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete an item from the menu.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(db_item)
    db.commit()
    return None