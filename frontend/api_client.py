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

    def get_users(self):
        try:
            tok = self._get_admin_token()
            if not tok:
                return []
            response = httpx.get(
                f"{self.base_url}/users/",
                headers={"Authorization": f"Bearer {tok}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def _get_admin_token(self):
        try:
            res = httpx.post(
                f"{self.base_url}/auth/login",
                json={"username": "admin"},
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return res.json().get("access_token")
        except Exception:
            pass
        return None

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
