from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from pydantic import BaseModel
import models
import schemas
import services
from database import get_db
from routers.auth import require_user, require_admin


class SetIngredientsRequest(BaseModel):
    ingredient_names: List[str]

# Lecture du menu : tout utilisateur connecté. Écriture : admin (voir chaque route).
router = APIRouter(
    prefix="/items",
    tags=["Items"],
    dependencies=[Depends(require_user)],
)


@router.post("/", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db),
                _admin: models.User = Depends(require_admin)):
    category = db.query(models.Category).filter(models.Category.id == item.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Associated category not found.")

    conflict = db.query(models.Item).filter(
        models.Item.name == item.name,
        models.Item.category_id == item.category_id,
        models.Item.deleted_at == None,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail=f"Item '{item.name}' already exists in this category.")

    new_item = models.Item(
        name=item.name,
        price=item.price,
        available=item.available,
        category_id=item.category_id,
        stock_quantity=item.stock_quantity,
    )
    db.add(new_item)
    db.flush()

    if item.options:
        for opt in item.options:
            db.add(models.ItemOption(
                item_id=new_item.id,
                name=opt.name,
                stock_quantity=opt.stock_quantity,
            ))

    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db),
                _admin: models.User = Depends(require_admin)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")

    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative.")

    if item_update.category_id is not None:
        cat = db.query(models.Category).filter(models.Category.id == item_update.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="New category not found.")

    if item_update.name is not None and item_update.name != db_item.name:
        target_cat = item_update.category_id or db_item.category_id
        conflict = db.query(models.Item).filter(
            models.Item.name == item_update.name,
            models.Item.category_id == target_cat,
            models.Item.id != item_id,
            models.Item.deleted_at == None,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Item '{item_update.name}' already exists in this category.")

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}/restore", response_model=schemas.ItemRead)
def restore_item(item_id: int, db: Session = Depends(get_db),
                 _admin: models.User = Depends(require_admin)):
    result = services.restore_item(db, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or not deleted.")
    return result


@router.get("/", response_model=List[schemas.ItemRead])
def list_items(include_deleted: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Item)
    if not include_deleted:
        query = query.filter(models.Item.deleted_at == None)
    return query.all()


@router.get("/{item_id}", response_model=schemas.ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return db_item


@router.put("/{item_id}/ingredients", response_model=schemas.ItemRead)
def set_item_ingredients(item_id: int, payload: SetIngredientsRequest, db: Session = Depends(get_db),
                         _admin: models.User = Depends(require_admin)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")

    db.query(models.ItemIngredient).filter(models.ItemIngredient.item_id == item_id).delete()

    for raw_name in payload.ingredient_names:
        name = raw_name.strip()
        if not name:
            continue
        ingredient = db.query(models.Ingredient).filter(models.Ingredient.name == name).first()
        if not ingredient:
            ingredient = models.Ingredient(name=name)
            db.add(ingredient)
            db.flush()
        db.add(models.ItemIngredient(item_id=item_id, ingredient_id=ingredient.id))

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db),
                _admin: models.User = Depends(require_admin)):
    result = services.soft_delete_item(db, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or already deleted.")
    return None


# ==========================================
# ITEM OPTIONS
# ==========================================

@router.post("/{item_id}/options", response_model=schemas.ItemOptionRead, status_code=status.HTTP_201_CREATED)
def create_item_option(item_id: int, option: schemas.ItemOptionCreate, db: Session = Depends(get_db),
                       _admin: models.User = Depends(require_admin)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    new_option = models.ItemOption(
        item_id=item_id,
        name=option.name,
        stock_quantity=option.stock_quantity,
    )
    db.add(new_option)
    db.commit()
    db.refresh(new_option)
    return new_option


@router.put("/options/{option_id}", response_model=schemas.ItemOptionRead)
def update_item_option(option_id: int, option_update: schemas.ItemOptionUpdate, db: Session = Depends(get_db),
                       _admin: models.User = Depends(require_admin)):
    db_option = db.query(models.ItemOption).filter(models.ItemOption.id == option_id).first()
    if not db_option:
        raise HTTPException(status_code=404, detail="Option not found.")
    update_data = option_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_option, key, value)
    db.commit()
    db.refresh(db_option)
    return db_option


@router.put("/options/{option_id}/restore", response_model=schemas.ItemOptionRead)
def restore_item_option(option_id: int, db: Session = Depends(get_db),
                        _admin: models.User = Depends(require_admin)):
    result = services.restore_item_option(db, option_id)
    if not result:
        raise HTTPException(status_code=404, detail="Option not found or not deleted.")
    return result


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_option(option_id: int, db: Session = Depends(get_db),
                       _admin: models.User = Depends(require_admin)):
    result = services.soft_delete_item_option(db, option_id)
    if not result:
        raise HTTPException(status_code=404, detail="Option not found or already deleted.")
    return None
