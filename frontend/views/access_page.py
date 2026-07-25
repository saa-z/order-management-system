from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt


class AccessPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("Gestion des acces")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)

        layout.addLayout(top_bar)

        layout.addStretch()
        placeholder = QLabel("Cette page est en cours de developpement.")
        placeholder.setStyleSheet("font-size: 16px; color: #6A6255;")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)
        layout.addStretch()
