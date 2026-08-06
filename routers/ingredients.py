from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

import models
import schemas
from database import get_db
from routers.auth import require_user, require_admin

# Lecture : tout utilisateur connecté (le POS en a besoin). Écriture : admin.
router = APIRouter(prefix="/ingredients", tags=["Ingredients"],
                   dependencies=[Depends(require_user)])


@router.get("/", response_model=List[schemas.IngredientRead])
def list_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).order_by(models.Ingredient.name).all()


@router.post("/", response_model=schemas.IngredientRead, status_code=status.HTTP_201_CREATED)
def create_ingredient(ingredient: schemas.IngredientCreate, db: Session = Depends(get_db),
                      _admin: models.User = Depends(require_admin)):
    existing = db.query(models.Ingredient).filter(models.Ingredient.name == ingredient.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists.")
    new = models.Ingredient(name=ingredient.name, is_base=ingredient.is_base)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.patch("/{ingredient_id}", response_model=schemas.IngredientRead)
def update_ingredient(ingredient_id: int, data: schemas.IngredientUpdate, db: Session = Depends(get_db),
                      _admin: models.User = Depends(require_admin)):
    ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found.")
    if data.name is not None:
        conflict = db.query(models.Ingredient).filter(
            models.Ingredient.name == data.name,
            models.Ingredient.id != ingredient_id,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Un ingrédient porte déjà ce nom.")
        ingredient.name = data.name
    if data.is_base is not None:
        ingredient.is_base = data.is_base
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db),
                      _admin: models.User = Depends(require_admin)):
    ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found.")
    try:
        db.delete(ingredient)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cet ingrédient est utilisé dans une commande passée et ne peut pas être supprimé.",
        )
    return None
