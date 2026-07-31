from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import services
from database import get_db
from routers.auth import require_user, require_admin

# Lecture du menu : tout utilisateur connecté. Écriture : admin (voir chaque route).
router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    dependencies=[Depends(require_user)],
)


def _build_filtered_category(cat: models.Category, include_deleted: bool) -> schemas.CategoryWithItems:
    items = cat.items if include_deleted else [i for i in cat.items if i.deleted_at is None]
    item_schemas = []
    for item in items:
        opts = item.options if include_deleted else [o for o in item.options if o.deleted_at is None]
        item_schemas.append(schemas.ItemRead(
            id=item.id,
            name=item.name,
            price=item.price,
            available=item.available,
            stock_quantity=item.stock_quantity,
            category_id=item.category_id,
            is_in_stock=item.is_in_stock,
            created_at=item.created_at,
            modified_at=item.modified_at,
            deleted_at=item.deleted_at,
            options=[
                schemas.ItemOptionRead(
                    id=o.id,
                    item_id=o.item_id,
                    name=o.name,
                    stock_quantity=o.stock_quantity,
                    created_at=o.created_at,
                    modified_at=o.modified_at,
                    deleted_at=o.deleted_at,
                )
                for o in opts
            ],
            ingredients=[
                schemas.IngredientRead(id=i.id, name=i.name, is_base=i.is_base)
                for i in item.ingredients
            ],
        ))

    active_items = [i for i in item_schemas if i.deleted_at is None]
    return schemas.CategoryWithItems(
        id=cat.id,
        name=cat.name,
        available=any(i.is_in_stock for i in active_items),
        created_at=cat.created_at,
        modified_at=cat.modified_at,
        deleted_at=cat.deleted_at,
        items=item_schemas,
    )


@router.post("/", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db),
                    _admin: models.User = Depends(require_admin)):
    exists = db.query(models.Category).filter(
        models.Category.name == category.name,
        models.Category.deleted_at == None,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail=f"Category '{category.name}' already exists.")
    new_cat = models.Category(name=category.name)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.put("/{category_id}", response_model=schemas.CategoryRead)
def update_category(category_id: int, category_update: schemas.CategoryUpdate, db: Session = Depends(get_db),
                    _admin: models.User = Depends(require_admin)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found.")

    if category_update.name is not None:
        conflict = db.query(models.Category).filter(
            models.Category.name == category_update.name,
            models.Category.id != category_id,
            models.Category.deleted_at == None,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Category '{category_update.name}' already exists.")
        db_category.name = category_update.name

    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/", response_model=List[schemas.CategoryWithItems])
def list_categories(include_deleted: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Category)
    if not include_deleted:
        query = query.filter(models.Category.deleted_at == None)
    categories = query.all()
    return [_build_filtered_category(cat, include_deleted) for cat in categories]


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db),
                    _admin: models.User = Depends(require_admin)):
    result = services.soft_delete_category(db, category_id)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found or already deleted.")
    return None


@router.put("/{category_id}/restore", response_model=schemas.CategoryRead)
def restore_category(category_id: int, db: Session = Depends(get_db),
                     _admin: models.User = Depends(require_admin)):
    result = services.restore_category(db, category_id)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found or not deleted.")
    return result
