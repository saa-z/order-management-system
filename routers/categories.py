from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.post("/", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Category).filter(models.Category.name == category.name).first()
    if exists:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category.name}' already exists."
        )
    new_cat = models.Category(name=category.name)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.put("/{category_id}", response_model=schemas.CategoryRead)
def update_category(category_id: int, category_update: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found.")

    if category_update.name is not None:
        exists = db.query(models.Category).filter(models.Category.name == category_update.name).first()
        if exists and exists.id != category_id:
            raise HTTPException(
                status_code=400,
                detail=f"Category '{category_update.name}' already exists."
            )

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/", response_model=List[schemas.CategoryWithItems])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found.")

    db.delete(db_category)
    db.commit()
    return None
