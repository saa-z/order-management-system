import sys
import os
import random

# Ensure the current directory is in Python's search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models

def init_db():
    print("⚠️  Resetting SQLite database...")

    # 1. Drop and recreate all tables to start with a clean database
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables recreated successfully.")

    db = SessionLocal()
    try:
        # 2. Definition of real categories
        categories_names = [
            "Boissons",
            "Alcools",
            "Pizzas",
            "Panozzos",
            "Salades",
            "Formules et Menus",
            "Desserts"
        ]

        db_categories = {}
        for nom in categories_names:
            cat = models.Categorie(nom=nom, disponible=True)
            db.add(cat)
            db.flush()
            db_categories[nom] = cat

        print(f"📂 {len(categories_names)} real categories created.")

        menu_items = [
            # --- PIZZAS ---
            {"nom": "Margherita", "prix": 8.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Napolitaine", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Norvégienne", "prix": 13.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "4 Fromages", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Reine", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Végétarienne", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Auvergnate", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "San Giorgio", "prix": 12.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Orientale", "prix": 11.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Kebab", "prix": 12.0, "disponible": True, "categorie": "Pizzas"},
            {"nom": "Ingrédient supplémentaire", "prix": 1.0, "disponible": True, "categorie": "Pizzas"},

            # --- PANOZZOS ---
            {"nom": "Panozzo Kebab", "prix": 9.0, "disponible": True, "categorie": "Panozzos"},
            {"nom": "Panozzo Auvergnat", "prix": 9.0, "disponible": True, "categorie": "Panozzos"},
            {"nom": "Panozzo Italien", "prix": 9.0, "disponible": True, "categorie": "Panozzos"},
            {"nom": "Panozzo Végétarien", "prix": 9.0, "disponible": True, "categorie": "Panozzos"},

            # --- SALADES ---
            {"nom": "Salade César", "prix": 12.0, "disponible": True, "categorie": "Salades"},
            {"nom": "Salade Chèvre chaud", "prix": 12.0, "disponible": True, "categorie": "Salades"},
            {"nom": "Salade San Giorgio", "prix": 13.0, "disponible": True, "categorie": "Salades"},

            # --- FORMULES & MENUS ---
            {"nom": "Menu : Panozzo + Boisson", "prix": 10.5, "disponible": True, "categorie": "Formules et Menus"},
            {
                "nom": "Menu Enfant (-10 ans) : Pizza Margherita/Pâtes + Dessert + Sirop au choix",
                "prix": 6.0,
                "disponible": True,
                "categorie": "Formules et Menus",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche"]
            },

            # --- BOISSONS (NON-ALCOHOLIC) ---
            {
                "nom": "Soda",
                "prix": 2.0,
                "disponible": True,
                "categorie": "Boissons",
                "options": ["Coca-Cola", "Coca 0", "Orangina", "Ice Tea"]
            },
            {"nom": "Eau pétillante", "prix": 1.5, "disponible": True, "categorie": "Boissons"},
            {"nom": "San Pellegrino", "prix": 2.0, "disponible": True, "categorie": "Boissons"},
            {
                "nom": "Sirop",
                "prix": 1.5,
                "disponible": True,
                "categorie": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche", "Orgeat","Mojito"]
            },
            {
                "nom": "Diabolo",
                "prix": 2.0,
                "disponible": True,
                "categorie": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche","Orgeat","Mojito"]
            },
            {"nom": "Mocktail", "prix": 2.0, "disponible": True, "categorie": "Boissons"},

            # --- ALCOHOLS ---
            {"nom": "Desperados", "prix": 2.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Bière 1664 (33cl)", "prix": 2.0, "disponible": True, "categorie": "Alcools"},
            {
                "nom": "Demi sirop",
                "prix": 3.0,
                "disponible": True,
                "categorie": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche", "Orgeat", "Mojito"]
            },
            {"nom": "Verre de vin (Rosé)", "prix": 2.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Verre de vin (Rouge)", "prix": 2.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Verre de vin (Blanc)", "prix": 2.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Pichet de vin (Rosé)", "prix": 7.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Pichet de vin (Rouge)", "prix": 7.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Pichet de vin (Blanc)", "prix": 7.5, "disponible": True, "categorie": "Alcools"},
            {"nom": "Bouteille de vin (Rosé)", "prix": 14.0, "disponible": True, "categorie": "Alcools"},
            {"nom": "Bouteille de vin (Rouge)", "prix": 14.0, "disponible": True, "categorie": "Alcools"},
            {"nom": "Bouteille de vin (Blanc)", "prix": 14.0, "disponible": True, "categorie": "Alcools"},
            {"nom": "Cocktail", "prix": 4.0, "disponible": True, "categorie": "Alcools"},

            # --- DESSERTS ---
            {
                "nom": "Glace (1 boule)",
                "prix": 2.5,
                "disponible": True,
                "categorie": "Desserts",
                "options": ["Vanille", "Citron", "Chocolat", "Fraise", "Cassis", "Framboise", "Pistache"]
            },
            {
                "nom": "Glace (2 boules)",
                "prix": 4.0,
                "disponible": True,
                "categorie": "Desserts",
                "options": ["Vanille", "Citron", "Chocolat", "Fraise", "Cassis", "Framboise", "Pistache"]
            },
            {"nom": "Part de dessert maison", "prix": 4.0, "disponible": True, "categorie": "Desserts"},
        ]

        # Link each item to its corresponding category using the retrieved ID
        for item in menu_items:
            cat_associee = db_categories.get(item["categorie"])
            if cat_associee:
                options_raw = item.get("options")
                options_dict = None
                stock_general = None

                # ⚠️ CHANGEMENT ICI : Si l'article a des options, on crée un dictionnaire {Option: Qté}
                if options_raw:
                    options_dict = {option: random.randint(0, 10) for option in options_raw}
                else:
                    # Si c'est un article classique (ex: Margherita), on lui colle un stock global aléatoire
                    stock_general = random.randint(0, 10)

                new_item = models.Item(
                    nom=item["nom"],
                    prix=item["prix"],
                    disponible=item["disponible"],
                    categorie_id=cat_associee.id,
                    options=options_dict,  # Nouveau format JSON : {"Coca-Cola": 4, "Ice Tea": 8}
                    quantite_en_stock=stock_general
                )
                db.add(new_item)

        # Save changes permanently to the database
        db.commit()
        print("🍕 All categories and real products have been successfully injected!")
        print("🎉 Your San Giorgio database was initiated!")

    except Exception as e:
        db.rollback()
        print(f"❌ An error occurred during database initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()