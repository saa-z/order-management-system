import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models
import schemas
import services

# Configuration de la base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Surcharge de la dépendance get_db pour utiliser la base de test
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ==========================================
# TEST SCENARIOS
# ==========================================

def test_manual_stock_adjustment():
    db = TestingSessionLocal()
    cat = models.Categorie(nom="Pizzas")
    db.add(cat)
    db.commit()
    item = models.Item(nom="Margherita", quantite_en_stock=10, categorie_id=cat.id, prix=10.0)
    db.add(item)
    db.commit()

    # Success: Adjust stock downwards
    services.adjust_inventory(db, item.id, 5)
    db.refresh(item) # Rafraîchir l'objet local après modification en base
    assert item.quantite_en_stock == 5
    assert item.disponible is True

    # Boundary: Adjust stock to 0
    services.adjust_inventory(db, item.id, 0)
    db.refresh(item)
    assert item.quantite_en_stock == 0
    assert item.disponible is False

def test_order_flow_success():
    db = TestingSessionLocal()
    cat = models.Categorie(nom="Boissons")
    db.add(cat)
    db.commit()
    item = models.Item(nom="Soda", quantite_en_stock=5, categorie_id=cat.id, prix=2.0)
    db.add(item)
    db.commit()

    # Place order for 2 items
    order_data = schemas.CommandeCreate(table=1, items=[schemas.CommandeItemCreate(item_id=item.id, quantite=2)])
    result = services.place_order(db, order_data)

    db.refresh(item) # Rafraîchir après la commande
    assert result is not None
    assert item.quantite_en_stock == 3

def test_order_failure_insufficient_stock():
    db = TestingSessionLocal()
    cat = models.Categorie(nom="Plats")
    db.add(cat)
    db.commit()
    item = models.Item(nom="Burger", quantite_en_stock=1, categorie_id=cat.id, prix=12.0)
    db.add(item)
    db.commit()

    # Try to order 5 items when only 1 is available
    order_data = schemas.CommandeCreate(table=1, items=[schemas.CommandeItemCreate(item_id=item.id, quantite=5)])
    result = services.place_order(db, order_data)

    assert result is None

def test_cancel_order_restores_stock():
    db = TestingSessionLocal()
    cat = models.Categorie(nom="Alcools")
    db.add(cat)
    db.commit()
    item = models.Item(nom="Vin", quantite_en_stock=10, categorie_id=cat.id, prix=20.0)
    db.add(item)
    db.commit()

    # Place order
    order_data = schemas.CommandeCreate(table=5, items=[schemas.CommandeItemCreate(item_id=item.id, quantite=3)])
    order = services.place_order(db, order_data)

    # Cancel order
    cancelled_order = services.cancel_order(db, order.id)
    db.expire_all()
    db.refresh(item)
    item_mis_a_jour = db.query(models.Item).filter(models.Item.id == item.id).first()
    assert cancelled_order.statut == "annulee"
    assert item_mis_a_jour.quantite_en_stock == 10