import sys
import os
import random
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models


def init_db():
    print("Resetting SQLite database...")

    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully.")

    db = SessionLocal()
    try:
        category_names = [
            "Boissons",
            "Alcools",
            "Pizzas",
            "Panozzos",
            "Salades",
            "Formules et Menus",
            "Desserts"
        ]

        db_categories = {}
        for name in category_names:
            cat = models.Category(name=name)
            db.add(cat)
            db.flush()
            db_categories[name] = cat

        print(f"{len(category_names)} categories created.")

        menu_items = [
            # --- PIZZAS ---
            {"name": "Margherita", "price": Decimal("8.00"), "available": True, "category": "Pizzas"},
            {"name": "Napolitaine", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "Norvégienne", "price": Decimal("13.00"), "available": True, "category": "Pizzas"},
            {"name": "4 Fromages", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "Reine", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "Végétarienne", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "Auvergnate", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "San Giorgio", "price": Decimal("12.00"), "available": True, "category": "Pizzas"},
            {"name": "Orientale", "price": Decimal("11.00"), "available": True, "category": "Pizzas"},
            {"name": "Kebab", "price": Decimal("12.00"), "available": True, "category": "Pizzas"},
            {"name": "Ingrédient supplémentaire", "price": Decimal("1.00"), "available": True, "category": "Pizzas"},

            # --- PANOZZOS ---
            {"name": "Panozzo Kebab", "price": Decimal("9.00"), "available": True, "category": "Panozzos"},
            {"name": "Panozzo Auvergnat", "price": Decimal("9.00"), "available": True, "category": "Panozzos"},
            {"name": "Panozzo Italien", "price": Decimal("9.00"), "available": True, "category": "Panozzos"},
            {"name": "Panozzo Végétarien", "price": Decimal("9.00"), "available": True, "category": "Panozzos"},

            # --- SALADES ---
            {"name": "Salade César", "price": Decimal("12.00"), "available": True, "category": "Salades"},
            {"name": "Salade Chèvre chaud", "price": Decimal("12.00"), "available": True, "category": "Salades"},
            {"name": "Salade San Giorgio", "price": Decimal("13.00"), "available": True, "category": "Salades"},

            # --- FORMULES & MENUS ---
            {"name": "Menu : Panozzo + Boisson", "price": Decimal("10.50"), "available": True, "category": "Formules et Menus"},
            {
                "name": "Menu Enfant (-10 ans) : Pizza Margherita/Pâtes + Dessert + Sirop au choix",
                "price": Decimal("6.00"),
                "available": True,
                "category": "Formules et Menus",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche"]
            },

            # --- BOISSONS ---
            {
                "name": "Soda",
                "price": Decimal("2.00"),
                "available": True,
                "category": "Boissons",
                "options": ["Coca-Cola", "Coca 0", "Orangina", "Ice Tea"]
            },
            {"name": "Eau pétillante", "price": Decimal("1.50"), "available": True, "category": "Boissons"},
            {"name": "San Pellegrino", "price": Decimal("2.00"), "available": True, "category": "Boissons"},
            {
                "name": "Sirop",
                "price": Decimal("1.50"),
                "available": True,
                "category": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche", "Orgeat", "Mojito"]
            },
            {
                "name": "Diabolo",
                "price": Decimal("2.00"),
                "available": True,
                "category": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche", "Orgeat", "Mojito"]
            },
            {"name": "Mocktail", "price": Decimal("2.00"), "available": True, "category": "Boissons"},

            # --- ALCOOLS ---
            {"name": "Desperados", "price": Decimal("2.50"), "available": True, "category": "Alcools"},
            {"name": "Bière 1664 (33cl)", "price": Decimal("2.00"), "available": True, "category": "Alcools"},
            {
                "name": "Demi sirop",
                "price": Decimal("3.00"),
                "available": True,
                "category": "Boissons",
                "options": ["Fraise", "Menthe", "Grenadine", "Citron", "Pêche", "Orgeat", "Mojito"]
            },
            {"name": "Verre de vin (Rosé)", "price": Decimal("2.50"), "available": True, "category": "Alcools"},
            {"name": "Verre de vin (Rouge)", "price": Decimal("2.50"), "available": True, "category": "Alcools"},
            {"name": "Verre de vin (Blanc)", "price": Decimal("2.50"), "available": True, "category": "Alcools"},
            {"name": "Pichet de vin (Rosé)", "price": Decimal("7.50"), "available": True, "category": "Alcools"},
            {"name": "Pichet de vin (Rouge)", "price": Decimal("7.50"), "available": True, "category": "Alcools"},
            {"name": "Pichet de vin (Blanc)", "price": Decimal("7.50"), "available": True, "category": "Alcools"},
            {"name": "Bouteille de vin (Rosé)", "price": Decimal("14.00"), "available": True, "category": "Alcools"},
            {"name": "Bouteille de vin (Rouge)", "price": Decimal("14.00"), "available": True, "category": "Alcools"},
            {"name": "Bouteille de vin (Blanc)", "price": Decimal("14.00"), "available": True, "category": "Alcools"},
            {"name": "Cocktail", "price": Decimal("4.00"), "available": True, "category": "Alcools"},

            # --- DESSERTS ---
            {
                "name": "Glace (1 boule)",
                "price": Decimal("2.50"),
                "available": True,
                "category": "Desserts",
                "options": ["Vanille", "Citron", "Chocolat", "Fraise", "Cassis", "Framboise", "Pistache"]
            },
            {
                "name": "Glace (2 boules)",
                "price": Decimal("4.00"),
                "available": True,
                "category": "Desserts",
                "options": ["Vanille", "Citron", "Chocolat", "Fraise", "Cassis", "Framboise", "Pistache"]
            },
            {"name": "Part de dessert maison", "price": Decimal("4.00"), "available": True, "category": "Desserts"},
        ]

        item_ingredient_map = {
            "Margherita":       ["Tomate", "Mozzarella", "Basilic", "Origan"],
            "Napolitaine":      ["Tomate", "Mozzarella", "Anchois", "Câpres", "Olives"],
            "Norvégienne":      ["Crème fraîche", "Mozzarella", "Saumon", "Aneth"],
            "4 Fromages":       ["Tomate", "Mozzarella", "Chèvre", "Bleu", "Parmesan"],
            "Reine":            ["Tomate", "Mozzarella", "Jambon", "Champignons"],
            "Végétarienne":     ["Tomate", "Mozzarella", "Poivrons", "Champignons", "Oignons", "Olives"],
            "Auvergnate":       ["Crème fraîche", "Mozzarella", "Bleu", "Lardons", "Pommes de terre"],
            "San Giorgio":      ["Tomate", "Mozzarella", "Jambon cru", "Roquette", "Parmesan"],
            "Orientale":        ["Tomate", "Mozzarella", "Merguez", "Oignons", "Poivrons"],
            "Kebab":            ["Tomate", "Mozzarella", "Kebab", "Oignons"],
            "Panozzo Kebab":       ["Kebab", "Oignons", "Salade", "Tomate"],
            "Panozzo Auvergnat":   ["Bleu", "Lardons", "Salade", "Tomate"],
            "Panozzo Italien":     ["Jambon cru", "Mozzarella", "Roquette", "Tomate"],
            "Panozzo Végétarien":  ["Poivrons", "Champignons", "Salade", "Tomate", "Mozzarella"],
        }

        ingredient_cache = {}

        def get_or_create_ingredient(name: str) -> models.Ingredient:
            if name in ingredient_cache:
                return ingredient_cache[name]
            ing = models.Ingredient(name=name)
            db.add(ing)
            db.flush()
            ingredient_cache[name] = ing
            return ing

        for item in menu_items:
            cat = db_categories.get(item["category"])
            if cat:
                options_raw = item.get("options")
                stock_general = None if options_raw else random.randint(5, 20)

                new_item = models.Item(
                    name=item["name"],
                    price=item["price"],
                    available=item["available"],
                    category_id=cat.id,
                    stock_quantity=stock_general,
                )
                db.add(new_item)
                db.flush()

                if options_raw:
                    for option_name in options_raw:
                        option = models.ItemOption(
                            item_id=new_item.id,
                            name=option_name,
                            stock_quantity=random.randint(5, 20),
                        )
                        db.add(option)

                for ingr_name in item_ingredient_map.get(item["name"], []):
                    ing = get_or_create_ingredient(ingr_name)
                    db.add(models.ItemIngredient(item_id=new_item.id, ingredient_id=ing.id))

        admin = models.User(username="admin", role=models.UserRole.ADMIN)
        db.add(admin)

        db.commit()
        print(f"{len(ingredient_cache)} ingredients created.")
        print("Admin user created (username: admin).")
        print("All categories, products and ingredients have been successfully injected!")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during database initialization: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
