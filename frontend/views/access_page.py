from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class AccessPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        title = QLabel("Gestion des accès")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()
        btn_refresh = QPushButton("Rafraichir")
        btn_refresh.setObjectName("btn-nav")
        btn_refresh.setFixedWidth(110)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_users)
        top_bar.addWidget(btn_refresh)
        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setFixedWidth(110)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)
        layout.addLayout(top_bar)

        # ── User list ──
        lbl_list = QLabel("Comptes enregistrés")
        lbl_list.setObjectName("section-header")
        layout.addWidget(lbl_list)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Identifiant", "Rôle", "Statut", "Créé le"])
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def load_users(self):
        users = self.api.get_users()
        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(u.get("username", "")))

            role_map = {"admin": "Administrateur", "server": "Serveur"}
            role_item = QTableWidgetItem(role_map.get(u.get("role", ""), u.get("role", "")))
            role_item.setTextAlignment(Qt.AlignCenter)
            if u.get("role") == "admin":
                role_item.setForeground(QColor("#D4A365"))
            self.table.setItem(row, 1, role_item)

            active = u.get("active", True)
            status_item = QTableWidgetItem("Actif" if active else "Inactif")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor("#2D6B45" if active else "#9C2A24"))
            self.table.setItem(row, 2, status_item)

            created = u.get("created_at", "")[:10] if u.get("created_at") else "—"
            date_item = QTableWidgetItem(created)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, date_item)
