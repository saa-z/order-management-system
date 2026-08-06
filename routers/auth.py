from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional

import models, schemas, services
from auth import create_access_token, decode_token
from database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

# Requêtes venant de la machine centrale (app desktop) → admin implicite, sans login.
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def is_remote(request: Request) -> bool:
    """Vrai si la requête vient d'un appareil distant (tablette/téléphone du LAN),
    donc PAS du central. Sert à décider si le central doit imprimer (file d'attente)."""
    host = request.client.host if request.client else None
    return host not in LOOPBACK_HOSTS


def _loopback_admin(db: Session) -> Optional[models.User]:
    return db.query(models.User).filter(
        models.User.role == models.UserRole.ADMIN,
        models.User.deleted_at == None,
    ).order_by(models.User.id).first()


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    # 1) Token valide présent → utilisateur du token (prioritaire).
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        user_id = decode_token(token)
        if user_id:
            user = db.query(models.User).filter(
                models.User.id == user_id,
                models.User.deleted_at == None,
            ).first()
            if user:
                return user
    # 2) Sinon, requête locale (central) → admin implicite (confiance physique).
    client_host = request.client.host if request.client else None
    if client_host in LOOPBACK_HOSTS:
        return _loopback_admin(db)
    return None


def require_user(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié")
    return user


def require_admin(user: models.User = Depends(require_user)) -> models.User:
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux administrateurs")
    return user


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = services.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserRead)
def me(user: models.User = Depends(require_user)):
    return user
