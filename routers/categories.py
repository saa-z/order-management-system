from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
import services

# We define the router with a prefix.
# Inside this file, "/" will automatically become "/categories/"
router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/", response_model=schemas.Categorie, status_code=status.HTTP_201_CREATED)
def create_category(categorie: schemas.CategorieCreate, db: Session = Depends(get_db)):
    """Create a new custom category."""
    exists = db.query(models.Categorie).filter(models.Categorie.nom == categorie.nom).first()
    if exists:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{categorie.nom}' already exists."
        )
    new_cat = models.Categorie(nom=categorie.nom)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.put("/{category_id}", response_model=schemas.Categorie)
def update_category(category_id: int, category_to_update: schemas.CategorieUpdate, db: Session = Depends(get_db)):
    """Update an existing category's name or availability status."""
    db_category = db.query(models.Categorie).filter(models.Categorie.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found.")

    if category_to_update.nom is not None:
        exists = db.query(models.Categorie).filter(models.Categorie.nom == category_to_update.nom).first()
        if exists and exists.id != category_id:
            raise HTTPException(
                status_code=400,
                detail=f"Category '{category_to_update.nom}' already exists."
            )

    update_data = category_to_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/", response_model=List[schemas.CategorieAvecItems])
def list_categories(db: Session = Depends(get_db)):
    """Retrieve all categories along with their respective items."""
    return db.query(models.Categorie).all()


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category and cascade delete its items."""
    db_category = db.query(models.Categorie).filter(models.Categorie.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found.")

    db.delete(db_category)
    db.commit()
    return None