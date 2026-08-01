import httpx


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.timeout = 5.0

    # ==========================================
    # ITEMS
    # ==========================================

    def get_items(self, include_deleted=False):
        try:
            params = {"include_deleted": str(include_deleted).lower()}
            response = httpx.get(f"{self.base_url}/items/", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching items: {e}")
            return []

    def create_item(self, payload):
        try:
            response = httpx.post(f"{self.base_url}/items/", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating item: {e}")
            return None

    def update_item(self, item_id, payload):
        try:
            response = httpx.put(f"{self.base_url}/items/{item_id}", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating item: {e}")
            return None

    def update_item_stock(self, item_id, quantity):
        return self.update_item(item_id, {"stock_quantity": quantity})

    def delete_item(self, item_id):
        try:
            response = httpx.delete(f"{self.base_url}/items/{item_id}", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting item: {e}")
            return False

    def restore_item(self, item_id):
        try:
            response = httpx.put(f"{self.base_url}/items/{item_id}/restore", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error restoring item: {e}")
            return None

    # ==========================================
    # ITEM OPTIONS
    # ==========================================

    def create_item_option(self, item_id, payload):
        try:
            response = httpx.post(
                f"{self.base_url}/items/{item_id}/options",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating item option: {e}")
            return None

    def update_item_option(self, option_id, payload):
        try:
            response = httpx.put(
                f"{self.base_url}/items/options/{option_id}",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating option: {e}")
            return None

    def update_option_stock(self, option_id, quantity):
        return self.update_item_option(option_id, {"stock_quantity": quantity})

    def delete_item_option(self, option_id):
        try:
            response = httpx.delete(
                f"{self.base_url}/items/options/{option_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting item option: {e}")
            return False

    def restore_item_option(self, option_id):
        try:
            response = httpx.put(
                f"{self.base_url}/items/options/{option_id}/restore",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error restoring item option: {e}")
            return None

    # ==========================================
    # CATEGORIES
    # ==========================================

    def get_categories(self, include_deleted=False):
        try:
            params = {"include_deleted": str(include_deleted).lower()}
            response = httpx.get(f"{self.base_url}/categories/", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def create_category(self, name):
        try:
            response = httpx.post(
                f"{self.base_url}/categories/",
                json={"name": name},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating category: {e}")
            return None

    def update_category(self, category_id, payload):
        try:
            response = httpx.put(
                f"{self.base_url}/categories/{category_id}",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating category: {e}")
            return None

    def delete_category(self, category_id):
        try:
            response = httpx.delete(
                f"{self.base_url}/categories/{category_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False

    def restore_category(self, category_id):
        try:
            response = httpx.put(
                f"{self.base_url}/categories/{category_id}/restore",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error restoring category: {e}")
            return None

    # ==========================================
    # ORDERS
    # ==========================================

    def get_orders(self):
        try:
            response = httpx.get(f"{self.base_url}/orders/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []

    def get_order(self, order_id):
        try:
            response = httpx.get(f"{self.base_url}/orders/{order_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching order: {e}")
            return None

    # ==========================================
    # PRINT JOBS (file d'impression — ouvrière du central)
    # ==========================================

    def get_print_jobs(self):
        try:
            response = httpx.get(f"{self.base_url}/print-jobs/",
                                 params={"status_filter": "pending"}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching print jobs: {e}")
            return []

    def mark_print_done(self, job_id):
        try:
            response = httpx.post(f"{self.base_url}/print-jobs/{job_id}/done", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error marking print job done: {e}")
            return False

    def create_order(self, order_data):
        try:
            response = httpx.post(f"{self.base_url}/orders/", json=order_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def get_last_order_id(self):
        try:
            response = httpx.get(f"{self.base_url}/orders/last", timeout=self.timeout)
            response.raise_for_status()
            if response.status_code == 204 or not response.text:
                return 0
            data = response.json()
            return data.get("id", 0)
        except Exception as e:
            print(f"Error fetching last order ID: {e}")
            return 0

    def add_order_items(self, order_id, items):
        try:
            response = httpx.post(
                f"{self.base_url}/orders/{order_id}/items",
                json={"items": items},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error adding items to order: {e}")
            return None

    # ==========================================
    # USERS
    # ==========================================
    # L'app desktop tape sur 127.0.0.1 → traitée comme admin par le backend
    # (confiance loopback), donc pas besoin de token ici.

    def get_users(self, include_revoked=False):
        try:
            params = {"include_revoked": str(include_revoked).lower()}
            response = httpx.get(f"{self.base_url}/users/", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def create_user(self, username, password, role="server"):
        try:
            response = httpx.post(
                f"{self.base_url}/users/",
                json={"username": username, "password": password, "role": role},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                return {"error": response.json().get("detail", "Erreur")}
            return response.json()
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def update_user(self, user_id, payload):
        try:
            response = httpx.put(
                f"{self.base_url}/users/{user_id}",
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                return {"error": response.json().get("detail", "Erreur")}
            return response.json()
        except Exception as e:
            print(f"Error updating user: {e}")
            return None

    def delete_user(self, user_id):
        try:
            response = httpx.delete(f"{self.base_url}/users/{user_id}", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def update_order_status(self, order_id, status):
        try:
            response = httpx.put(
                f"{self.base_url}/orders/{order_id}/status",
                json={"status": status},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating order status: {e}")
            return None

    # ==========================================
    # INGREDIENTS
    # ==========================================

    def get_ingredients(self):
        try:
            response = httpx.get(f"{self.base_url}/ingredients/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching ingredients: {e}")
            return []

    def set_item_ingredients(self, item_id, ingredient_names):
        try:
            response = httpx.put(
                f"{self.base_url}/items/{item_id}/ingredients",
                json={"ingredient_names": ingredient_names},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error setting item ingredients: {e}")
            return None

    def create_ingredient(self, name, is_base=False):
        try:
            response = httpx.post(
                f"{self.base_url}/ingredients/",
                json={"name": name, "is_base": is_base},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating ingredient: {e}")
            return None

    def update_ingredient(self, ingredient_id, payload):
        try:
            response = httpx.patch(
                f"{self.base_url}/ingredients/{ingredient_id}",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating ingredient: {e}")
            return None

    def delete_ingredient(self, ingredient_id):
        try:
            response = httpx.delete(
                f"{self.base_url}/ingredients/{ingredient_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting ingredient: {e}")
            return False
