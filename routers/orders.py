from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from fastapi import Request

import models
import schemas
import services
from database import get_db
from routers.auth import get_current_user, require_user, is_remote

# Prise de commande + historique : accessibles aux deux rôles (admin et server).
router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(require_user)],
)


@router.post("/", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    user_id = current_user.id if current_user else None
    result = services.place_order(db, order, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Order could not be created. Check item availability and stock."
        )
    # Commande prise depuis un appareil distant → le central imprime le bon cuisine.
    if is_remote(request):
        services.queue_print_job(db, result.id, "kitchen", batch=1)
    return result


@router.get("/", response_model=List[schemas.OrderRead])
def list_orders(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if status_filter:
        query = query.filter(models.Order.status == status_filter)
    return query.order_by(models.Order.created_at.desc()).all()


@router.get("/last", response_model=Optional[schemas.OrderRead])
def get_last_order(db: Session = Depends(get_db)):
    return db.query(models.Order).order_by(models.Order.id.desc()).first()


@router.get("/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return db_order


@router.put("/{order_id}/status", response_model=schemas.OrderRead)
def update_order_status(order_id: int, status_update: schemas.OrderUpdateStatus,
                        request: Request, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")

    prev = db_order.status
    db_order.status = status_update.status
    db.commit()
    db.refresh(db_order)

    # Depuis un appareil distant : facturer → reçu ; annuler → bon d'annulation.
    if is_remote(request) and status_update.status != prev:
        if status_update.status == models.OrderStatus.PAID:
            services.queue_print_job(db, order_id, "receipt")
        elif status_update.status == models.OrderStatus.CANCELLED:
            services.queue_print_job(db, order_id, "cancel")
    return db_order


@router.post("/{order_id}/items", response_model=schemas.OrderRead)
def add_items_to_order(order_id: int, items_update: schemas.OrderUpdateItems,
                       request: Request, db: Session = Depends(get_db)):
    result = services.add_items_to_order(db, order_id, items_update.items)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Could not add items. Order may be closed or stock insufficient."
        )
    # Nouveau bon depuis un appareil distant → le central imprime ce bon.
    if is_remote(request):
        max_batch = max((it.batch or 1) for it in result.items) if result.items else 1
        services.queue_print_job(db, order_id, "kitchen", batch=max_batch)
    return result


@router.post("/{order_id}/reprint", response_model=schemas.PrintJobRead, status_code=status.HTTP_201_CREATED)
def reprint(order_id: int, job_type: str = "kitchen", batch: Optional[int] = None,
            db: Session = Depends(get_db)):
    """Demande de (ré)impression manuelle (bouton « Imprimer bon(s) » / « Facturer »)."""
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return services.queue_print_job(db, order_id, job_type, batch=batch)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    result = services.cancel_order(db, order_id)
    if not result:
        raise HTTPException(status_code=404, detail="Order not found or already cancelled.")
    return None
