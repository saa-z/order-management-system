# San Giorgio — OMS

Order Management System for the San Giorgio pizzeria. A local desktop application built with a FastAPI REST backend and a PySide6 graphical interface.

---

## Features

| Module | Description |
|---|---|
| **Point of Sale (POS)** | Place orders by category/item, select options, add per-item comments, choose order type (eat-in / take-away) |
| **Stock Management** | Manually adjust stock levels per item and per option |
| **Order Tracking** | Real-time kitchen view, status transitions (pending → in kitchen → ready → paid / cancelled) |
| **Order History** | Full order history with item details, prices, options, and name snapshots |
| **Item Management** | Full CRUD on categories, items, and options; soft delete with restore support |
| **Printing** | Printable receipt (72 mm format) via QPrinter |

---

## Architecture

```
order-management-system/
├── main.py            # FastAPI entry point, lifespan, CORS
├── database.py        # SQLAlchemy / SQLite connection
├── models.py          # ORM models (Category, Item, ItemOption, Order, …)
├── schemas.py         # Pydantic v2 schemas (read / write)
├── services.py        # Business logic (order placement, soft delete, stock)
├── init_db.py         # DB reset and seed script
├── test-api.py        # Functional test suite
├── routers/
│   ├── categories.py  # GET/POST/PUT/DELETE /categories
│   ├── items.py       # GET/POST/PUT/DELETE /items and /items/options
│   └── orders.py      # GET/POST/PUT /orders
└── frontend/
    ├── main.py            # Qt application entry point
    ├── api_client.py      # httpx wrapper for the backend
    ├── styles.qss         # QSS theme (brown / cream / gold palette)
    └── views/
        ├── main_window.py          # Main window + QStackedWidget navigation
        ├── home_page.py            # Home page
        ├── menu_page.py            # Navigation menu
        ├── pos_order_page.py       # POS order interface
        ├── stock_page.py           # Stock management
        ├── manage_items_page.py    # Item management (3-panel CRUD)
        ├── history_page.py         # Order history
        ├── access_page.py          # Access / settings page
        ├── order_type_dialog.py    # Order type dialog
        └── option_picker_dialog.py # Option selection dialog
```

---

## Data Model

```
Category ──< Item ──< ItemOption
                └──< OrderItem ──< OrderItemOption
Order ──< OrderItem
```

- **Soft delete**: `deleted_at` (nullable datetime) on `Category`, `Item`, and `ItemOption`. Deleting a category cascades to its items and their options.
- **History snapshots**: `item_name_snapshot` on `OrderItem` and `option_name_snapshot` on `OrderItemOption` — renaming an item or option never affects past orders.
- **Prices**: stored as `Decimal` (not float).
- **Stock**: `stock_quantity = NULL` means unlimited stock. For items with options, stock is tracked per option rather than on the item itself.

---

## Requirements

- Python 3.11+
- pip

---

## Installation

```bash
cd order-management-system

# Create and activate the virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic httpx PySide6
```

---

## Running the app

### 1. Initialize the database

Run once, or any time you want to reset to a clean state with demo data:

```bash
python init_db.py
```

### 2. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000`. Interactive docs are at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

```bash
cd frontend
python main.py
```

---

## API Reference

### Categories

| Method | Route | Description |
|---|---|---|
| `GET` | `/categories/` | List categories with nested items and options |
| `GET` | `/categories/?include_deleted=true` | Include soft-deleted records |
| `POST` | `/categories/` | Create a category |
| `PUT` | `/categories/{id}` | Rename a category |
| `DELETE` | `/categories/{id}` | Soft delete (cascades to items and options) |
| `PUT` | `/categories/{id}/restore` | Restore a soft-deleted category |

### Items

| Method | Route | Description |
|---|---|---|
| `POST` | `/items/` | Create an item |
| `PUT` | `/items/{id}` | Update an item |
| `DELETE` | `/items/{id}` | Soft delete (cascades to options) |
| `PUT` | `/items/{id}/restore` | Restore a soft-deleted item |
| `POST` | `/items/{id}/options` | Add an option to an item |
| `PUT` | `/items/options/{id}` | Update an option |
| `DELETE` | `/items/options/{id}` | Soft delete an option |
| `PUT` | `/items/options/{id}/restore` | Restore a soft-deleted option |

### Orders

| Method | Route | Description |
|---|---|---|
| `GET` | `/orders/` | List all orders |
| `GET` | `/orders/last` | Get the most recent order |
| `POST` | `/orders/` | Place an order (decrements stock) |
| `PUT` | `/orders/{id}/status` | Update an order's status |

---

## Tests

A functional test script covers the main flows:

```bash
python test-api.py
```

Scenarios covered:
- Manual stock adjustment
- Full order flow (create → kitchen → paid)
- Order rejection on insufficient stock
- Order with options
- Order cancellation and stock restoration

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 (Mapped / mapped_column) |
| Database | SQLite |
| Validation | Pydantic v2 |
| HTTP client | httpx |
| GUI framework | PySide6 (Qt 6) |
| UI theme | QSS (objectName-based) |
| Printing | QPrinter + QPrintDialog |
