from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt


STATUS_LABELS = {
    "pending": "En attente",
    "in_kitchen": "En cuisine",
    "ready": "Pret",
    "paid": "Payee",
    "cancelled": "Annulee",
}

STATUS_COLORS = {
    "pending": "#B88647",
    "in_kitchen": "#E67E22",
    "ready": "#2D6B45",
    "paid": "#5A5550",
    "cancelled": "#9C2A24",
}

ORDER_TYPE_LABELS = {
    "eat_in": "Sur place",
    "take_away": "A emporter",
}


class HistoryPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("Historique des commandes")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_refresh = QPushButton("Rafraichir")
        btn_refresh.setObjectName("btn-secondary")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_history)
        top_bar.addWidget(btn_refresh)

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)

        layout.addLayout(top_bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Type", "Total", "Statut"])
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def load_history(self):
        try:
            orders = self.api.get_orders()
            self.table.setRowCount(0)

            for order in orders:
                row = self.table.rowCount()
                self.table.insertRow(row)

                id_item = QTableWidgetItem(str(order.get("id", "")))
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 0, id_item)

                date_raw = str(order.get("created_at", ""))
                date_display = date_raw[:16].replace("T", " ") if "T" in date_raw else date_raw
                date_item = QTableWidgetItem(date_display)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 1, date_item)

                type_text = ORDER_TYPE_LABELS.get(order.get("order_type", ""), order.get("order_type", ""))
                type_item = QTableWidgetItem(type_text)
                type_item.setTextAlignment(Qt.AlignCenter)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 2, type_item)

                price_item = QTableWidgetItem(f"{order.get('total_price', 0):.2f} €")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 3, price_item)

                status_key = order.get("status", "")
                status_text = STATUS_LABELS.get(status_key, status_key)
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                from PySide6.QtGui import QColor
                color = STATUS_COLORS.get(status_key, "#F5F1E6")
                status_item.setForeground(QColor(color))
                self.table.setItem(row, 4, status_item)

        except Exception as e:
            print(f"Could not load history: {e}")
