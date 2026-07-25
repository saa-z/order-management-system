from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


@router.post("/", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == item.category_id).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Associated category not found. Please create it first."
        )

    new_item = models.Item(
        name=item.name,
        price=item.price,
        available=item.available,
        category_id=item.category_id,
        stock_quantity=item.stock_quantity,
        options=item.options,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")

    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="The stock quantity cannot be negative."
        )

    if item_update.category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == item_update.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="The specified new category does not exist.")

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[schemas.ItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()


@router.get("/{item_id}", response_model=schemas.ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(db_item)
    db.commit()
    return None
