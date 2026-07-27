import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models
import schemas
import services

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def test_manual_stock_adjustment():
    db = TestingSessionLocal()
    cat = models.Category(name="Pizzas")
    db.add(cat)
    db.commit()
    item = models.Item(name="Margherita", stock_quantity=10, category_id=cat.id, price=Decimal("10.00"))
    db.add(item)
    db.commit()

    services.adjust_inventory(db, item.id, 5)
    db.refresh(item)
    assert item.stock_quantity == 5
    assert item.is_in_stock is True

    services.adjust_inventory(db, item.id, 0)
    db.refresh(item)
    assert item.stock_quantity == 0
    assert item.is_in_stock is False
    assert item.available is True


def test_order_flow_success():
    db = TestingSessionLocal()
    cat = models.Category(name="Boissons")
    db.add(cat)
    db.commit()
    item = models.Item(name="Soda", stock_quantity=5, category_id=cat.id, price=Decimal("2.00"))
    db.add(item)
    db.commit()

    order_data = schemas.OrderCreate(
        table_number=1, covers=2, seating_location="indoor",
        items=[schemas.OrderItemCreate(item_id=item.id, quantity=2)]
    )
    result = services.place_order(db, order_data)

    db.refresh(item)
    assert result is not None
    assert item.stock_quantity == 3
    assert result.total_price == Decimal("4.00")


def test_order_failure_insufficient_stock():
    db = TestingSessionLocal()
    cat = models.Category(name="Plats")
    db.add(cat)
    db.commit()
    item = models.Item(name="Burger", stock_quantity=1, category_id=cat.id, price=Decimal("12.00"))
    db.add(item)
    db.commit()

    order_data = schemas.OrderCreate(
        table_number=1, covers=2, seating_location="indoor",
        items=[schemas.OrderItemCreate(item_id=item.id, quantity=5)]
    )
    result = services.place_order(db, order_data)

    assert result is None


def test_order_with_selected_options():
    db = TestingSessionLocal()
    cat = models.Category(name="Boissons")
    db.add(cat)
    db.commit()
    item = models.Item(
        name="Soda",
        stock_quantity=10,
        category_id=cat.id,
        price=Decimal("2.00"),
    )
    db.add(item)
    db.flush()

    opt_coca = models.ItemOption(item_id=item.id, name="Coca-Cola", stock_quantity=5)
    opt_orangina = models.ItemOption(item_id=item.id, name="Orangina", stock_quantity=5)
    db.add_all([opt_coca, opt_orangina])
    db.commit()

    order_data = schemas.OrderCreate(
        table_number=1, covers=2, seating_location="indoor",
        items=[schemas.OrderItemCreate(
            item_id=item.id,
            quantity=5,
            selected_options=[
                schemas.OrderItemOptionCreate(item_option_id=opt_coca.id, quantity=3),
                schemas.OrderItemOptionCreate(item_option_id=opt_orangina.id, quantity=2),
            ],
        )]
    )
    result = services.place_order(db, order_data)

    assert result is not None
    assert result.total_price == Decimal("10.00")
    assert result.items[0].quantity == 5
    assert len(result.items[0].selected_options) == 2

    db.refresh(opt_coca)
    db.refresh(opt_orangina)
    assert opt_coca.stock_quantity == 2
    assert opt_orangina.stock_quantity == 3


def test_cancel_order_restores_stock():
    db = TestingSessionLocal()
    cat = models.Category(name="Alcools")
    db.add(cat)
    db.commit()
    item = models.Item(name="Vin", stock_quantity=10, category_id=cat.id, price=Decimal("20.00"))
    db.add(item)
    db.commit()

    order_data = schemas.OrderCreate(
        table_number=5, covers=3, seating_location="outdoor",
        items=[schemas.OrderItemCreate(item_id=item.id, quantity=3)]
    )
    order = services.place_order(db, order_data)

    cancelled_order = services.cancel_order(db, order.id)
    db.expire_all()
    db.refresh(item)
    updated_item = db.query(models.Item).filter(models.Item.id == item.id).first()
    assert cancelled_order.status == models.OrderStatus.CANCELLED
    assert updated_item.stock_quantity == 10


def test_cancel_order_restores_option_stock():
    db = TestingSessionLocal()
    cat = models.Category(name="Boissons")
    db.add(cat)
    db.commit()
    item = models.Item(name="Soda", stock_quantity=10, category_id=cat.id, price=Decimal("2.00"))
    db.add(item)
    db.flush()

    opt = models.ItemOption(item_id=item.id, name="Coca-Cola", stock_quantity=5)
    db.add(opt)
    db.commit()

    order_data = schemas.OrderCreate(
        table_number=1, covers=1, seating_location="indoor",
        items=[schemas.OrderItemCreate(
            item_id=item.id,
            quantity=3,
            selected_options=[
                schemas.OrderItemOptionCreate(item_option_id=opt.id, quantity=3),
            ],
        )]
    )
    order = services.place_order(db, order_data)
    assert order is not None

    db.refresh(opt)
    assert opt.stock_quantity == 2

    services.cancel_order(db, order.id)
    db.expire_all()
    db.refresh(opt)
    assert opt.stock_quantity == 5
