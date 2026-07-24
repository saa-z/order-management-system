from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer

class HomePage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Bienvenue chez San Giorgio"))
        layout.addWidget(QLabel("Chargement..."))
        self.setLayout(layout)

        QTimer.singleShot(3000, self.go_to_menu)


    def go_to_menu(self):
            # Utilise la fenêtre principale pour changer de page
            self.main_window.go_to("MENU")