from PySide6.QtWidgets import QMainWindow, QStackedWidget
from api_client import ApiClient

# Import all view classes
from views.home_page import HomePage
from views.menu_page import MenuPage
from views.pos_order_page import PosOrderPage
from views.stock_page import StockPage
from views.manage_items_page import ManageItemsPage
from views.history_page import HistoryPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Interface setup (French title)
        self.setWindowTitle("San Giorgio - OMS")
        self.setMinimumSize(1024, 768)

        # Initialize the API client once
        self.api_client = ApiClient()

        # Initialize the stack widget for navigation
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Dictionary of pages for easy navigation
        # We pass 'self' (the window) for navigation (go_to)
        # We pass 'self.api_client' for data operations
        self.pages = {
            "HOME": HomePage(self, self.api_client),
            "MENU": MenuPage(self, self.api_client),
            "ORDER": PosOrderPage(self, self.api_client),
            "STOCK": StockPage(self, self.api_client),
            "ITEMS": ManageItemsPage(self, self.api_client),
            "HISTORY": HistoryPage(self, self.api_client)
        }

        # Register pages to the stack
        for name, widget in self.pages.items():
            self.stack.addWidget(widget)

        # Set the starting page
        self.go_to("HOME")

    def go_to(self, page_name):
        """Navigate to a specific page by name."""
        if page_name in self.pages:
            self.stack.setCurrentWidget(self.pages[page_name])