import httpx


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.timeout = 5.0  # Timeout de 5 secondes

    def get_items(self):
        """Fetch all items from the database via FastAPI."""
        try:
            # On ajoute un timeout pour éviter de bloquer l'interface
            response = httpx.get(f"{self.base_url}/items/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # Erreur renvoyée par le serveur (ex: 404, 500)
            print(f"Erreur HTTP : {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            # Erreur de connexion (ex: serveur éteint, pas d'internet)
            print(f"Erreur de connexion : {e}")
            return []
        except Exception as e:
            # Sécurité pour toute autre erreur imprévue
            print(f"Erreur inattendue : {e}")
            return []

    def create_order(self, order_data):
        """Send a new order to the backend."""
        try:
            response = httpx.post(f"{self.base_url}/orders/", json=order_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur lors de la création de la commande : {e}")
            return None

    def get_categories(self):
        """Fetch categories and their items from the API."""
        try:
            # We call the /categories/ endpoint
            response = httpx.get(f"{self.base_url}/categories/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return []
        except httpx.RequestError as e:
            print(f"Connection error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def get_orders(self):
        """Fetch all orders from the API."""
        try:
            response = httpx.get(f"{self.base_url}/orders/", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []


def get_last_order_id(self):
    try:
        response = httpx.get(f"{self.base_url}/orders/last", timeout=self.timeout)
        response.raise_for_status()

        if response.status_code == 204 or not response.text:
            return 0

        data = response.json()
        return data.get('id', 0)
    except Exception as e:
        print(f"Error fetching last order ID: {e}")
        return 0

def update_stock(self, item_id, quantity):
    try:
        url = f"{self.base_url}/items/{item_id}"
        payload = {"quantite_en_stock": quantity}
        response = httpx.patch(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la mise à jour du stock : {e}")

