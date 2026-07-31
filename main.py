import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

import models
from database import engine
from routers import categories, items, orders
from routers import auth as auth_router
from routers import users as users_router
from routers import ingredients as ingredients_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="San Giorgio - Order API",
    description="Local API for the San Giorgio Pizzeria order-taking application",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(orders.router)
app.include_router(ingredients_router.router)


@app.get("/")
def read_root():
    # Racine → page web (login). L'API reste sous ses préfixes (/auth, /orders, …).
    return RedirectResponse(url="/web/login.html")


web_dir = os.path.join(os.path.dirname(__file__), "web")
os.makedirs(web_dir, exist_ok=True)
app.mount("/web", StaticFiles(directory=web_dir, html=True), name="web")
