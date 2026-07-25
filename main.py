from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import models
from database import engine, SessionLocal
from routers import categories, items, orders

models.Base.metadata.create_all(bind=engine)

DEFAULT_CATEGORIES = [
    "Boissons",
    "Boissons chaudes",
    "Alcools",
    "Pizzas",
    "Panozzos",
    "Salades",
    "Burgers",
    "Plats",
    "Desserts"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        for cat_name in DEFAULT_CATEGORIES:
            exists = db.query(models.Category).filter(models.Category.name == cat_name).first()
            if not exists:
                new_cat = models.Category(name=cat_name)
                db.add(new_cat)
        db.commit()
        print("Default categories checked/inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during category initialization: {e}")
    finally:
        db.close()
    yield


app = FastAPI(
    title="San Giorgio - Order API",
    description="Local API for the San Giorgio Pizzeria order-taking application",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(items.router)
app.include_router(orders.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to San Giorgio Order API. The backend is running."}
