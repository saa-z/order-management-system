from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models, schemas, services
from routers.auth import require_admin
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[schemas.UserRead])
def list_users(
    include_revoked: bool = False,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return services.list_users(db, include_revoked=include_revoked)


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: schemas.UserCreate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = services.create_user(db, data)
    if not user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
    return user


@router.put("/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: int,
    data: schemas.UserUpdate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = services.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé ou nom déjà pris")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte")
    if not services.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
