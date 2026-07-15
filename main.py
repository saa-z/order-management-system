from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import models
from database import engine, SessionLocal
from routers import categories, items, commandes

# Generate database tables in the SQLite database if they don't exist yet
models.Base.metadata.create_all(bind=engine)

# List of default categories to be automatically created on startup
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

# Application lifecycle management (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes on application startup.
    Automatically inserts default categories into the SQLite database if they do not exist.
    """
    db = SessionLocal()
    try:
        for cat_name in DEFAULT_CATEGORIES:
            exists = db.query(models.Categorie).filter(models.Categorie.nom == cat_name).first()
            if not exists:
                new_cat = models.Categorie(nom=cat_name)
                db.add(new_cat)
        db.commit()
        print("Default categories checked/inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during category initialization: {e}")
    finally:
        db.close()
    yield

# Initialize FastAPI with our custom lifespan manager
app = FastAPI(
    title="San Giorgio - Order API",
    description="Local API for the San Giorgio Pizzeria order-taking application",
    lifespan=lifespan
)

# --- ADDED: CORS Middleware ---
# This allows your Android app to connect to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include all the modular routers
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(commandes.router)

# --- ADDED: Root endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to San Giorgio Order API. The backend is running."}