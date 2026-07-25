from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import QTimer, Qt


class HomePage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout()
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setAlignment(Qt.AlignCenter)

        layout.addStretch(2)

        title = QLabel("SAN GIORGIO")
        title.setObjectName("brand-title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedWidth(200)
        sep_layout = QVBoxLayout()
        sep_layout.setAlignment(Qt.AlignCenter)
        sep_layout.addWidget(separator, alignment=Qt.AlignCenter)
        layout.addLayout(sep_layout)

        subtitle = QLabel("PIZZERIA  ·  RESTAURANT ITALIEN")
        subtitle.setObjectName("brand-subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        location = QLabel("Saint-Georges-de-Mons")
        location.setStyleSheet("font-size: 13px; color: #6A6255;")
        location.setAlignment(Qt.AlignCenter)
        layout.addWidget(location)

        layout.addStretch(3)

        loading = QLabel("Chargement...")
        loading.setStyleSheet("font-size: 12px; color: #5A5550;")
        loading.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading)

        self.setLayout(layout)
        QTimer.singleShot(2500, self.go_to_menu)

    def go_to_menu(self):
        self.main_window.go_to("MENU")
