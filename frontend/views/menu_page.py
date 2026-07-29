from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt


class MenuPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 30, 40, 30)

        header = QHBoxLayout()
        title = QLabel("SAN GIORGIO")
        title.setObjectName("page-title")
        header.addWidget(title)
        header.addStretch()
        outer.addLayout(header)

        subtitle = QLabel("Que souhaitez-vous faire ?")
        subtitle.setObjectName("page-subtitle")
        outer.addWidget(subtitle)

        outer.addSpacing(20)

        grid = QGridLayout()
        grid.setSpacing(16)

        btn_order = QPushButton("Prendre commande")
        btn_order.setObjectName("menu-card-primary")
        btn_order.setMinimumHeight(100)
        btn_order.setCursor(Qt.PointingHandCursor)
        btn_order.clicked.connect(lambda: self.main_window.go_to("ORDER"))
        grid.addWidget(btn_order, 0, 0)

        btn_history = QPushButton("Historique des commandes")
        btn_history.setObjectName("menu-card-primary")
        btn_history.setMinimumHeight(100)
        btn_history.setCursor(Qt.PointingHandCursor)
        btn_history.clicked.connect(lambda: self.main_window.go_to("HISTORY"))
        grid.addWidget(btn_history, 0, 1)

        btn_stock = QPushButton("Gestion des stocks")
        btn_stock.setObjectName("menu-card")
        btn_stock.setMinimumHeight(80)
        btn_stock.setCursor(Qt.PointingHandCursor)
        btn_stock.clicked.connect(lambda: self.main_window.go_to("STOCK"))
        grid.addWidget(btn_stock, 1, 0)

        btn_items = QPushButton("Gestion des articles")
        btn_items.setObjectName("menu-card")
        btn_items.setMinimumHeight(80)
        btn_items.setCursor(Qt.PointingHandCursor)
        btn_items.clicked.connect(lambda: self.main_window.go_to("ITEMS"))
        grid.addWidget(btn_items, 1, 1)

        btn_access = QPushButton("Gestion des acces")
        btn_access.setObjectName("menu-card")
        btn_access.setMinimumHeight(80)
        btn_access.setCursor(Qt.PointingHandCursor)
        btn_access.clicked.connect(lambda: self.main_window.go_to("ACCESS"))
        grid.addWidget(btn_access, 2, 0)

        outer.addLayout(grid, stretch=1)
        outer.addStretch()
