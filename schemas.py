from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# ==========================================
# 1. ITEMS
# ==========================================

class ItemBase(BaseModel):
    nom: str
    prix: float
    disponible: bool = True
    quantite_en_stock: Optional[int] = None
    categorie_id: int
    last_modified: Optional[datetime] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    nom: Optional[str] = None
    prix: Optional[float] = None
    disponible: Optional[bool] = None
    quantite_en_stock: Optional[int] = None
    categorie_id: Optional[int] = None
    last_modified: Optional[datetime] = None

class Item(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. COMMANDE ITEMS (Lignes de commande)
# ==========================================

class CommandeItemBase(BaseModel):
    item_id: int
    quantite: int = 1
    commentaire: Optional[str] = None

class CommandeItemCreate(CommandeItemBase):
    pass

class CommandeItem(CommandeItemBase):
    id: int
    commande_id: int
    item: Item  # Utilisé pour retourner les détails de l'item dans la commande

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. CATEGORIES
# ==========================================

class CategorieBase(BaseModel):
    nom: str
    disponible: bool = True

class CategorieCreate(CategorieBase):
    pass

class CategorieUpdate(BaseModel):
    nom: Optional[str] = None
    disponible: Optional[bool] = None

class Categorie(CategorieBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CategorieAvecItems(Categorie):
    items: List[Item] = []


# ==========================================
# 4. COMMANDES (Orders)
# ==========================================

class CommandeBase(BaseModel):
    table: int

class CommandeCreate(CommandeBase):
    items: List[CommandeItemCreate]

class CommandeUpdateStatus(BaseModel):
    statut: str

class CommandeUpdateTable(BaseModel):
    table: int

class CommandeUpdateItems(BaseModel):
    items: List[CommandeItemCreate]

class Commande(CommandeBase):
    id: int
    statut: str
    date_creation: datetime
    items: List[CommandeItem] = []

    model_config = ConfigDict(from_attributes=True)