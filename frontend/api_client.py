import httpx


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.timeout = 5.0

    def get_items(self):
        try:
            response = httpx.get(f"{self.base_url}/items/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching items: {e}")
            return []

    def get_categories(self):
        try:
            response = httpx.get(f"{self.base_url}/categories/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

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

    def update_stock_raw(self, item_id, payload):
        return self.update_item(item_id, payload)
