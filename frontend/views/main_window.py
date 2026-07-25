from PySide6.QtWidgets import QMainWindow, QStackedWidget
from api_client import ApiClient

from views.home_page import HomePage
from views.menu_page import MenuPage
from views.pos_order_page import PosOrderPage
from views.stock_page import StockPage
from views.manage_items_page import ManageItemsPage
from views.history_page import HistoryPage
from views.access_page import AccessPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("San Giorgio — OMS")
        self.setMinimumSize(1024, 768)

        self.api_client = ApiClient()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.pages = {
            "HOME": HomePage(self, self.api_client),
            "MENU": MenuPage(self, self.api_client),
            "ORDER": PosOrderPage(self, self.api_client),
            "STOCK": StockPage(self, self.api_client),
            "ITEMS": ManageItemsPage(self, self.api_client),
            "HISTORY": HistoryPage(self, self.api_client),
            "ACCESS": AccessPage(self, self.api_client),
        }

        for name, widget in self.pages.items():
            self.stack.addWidget(widget)

        self.go_to("HOME")

    def go_to(self, page_name):
        if page_name in self.pages:
            self.stack.setCurrentWidget(self.pages[page_name])
