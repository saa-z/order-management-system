from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton


class MenuPage(QWidget):
    def __init__(self, main_window, api_client):
        """
        Initialize the Menu Page.
        :param main_window: Reference to the MainWindow for navigation.
        :param api_client: Reference to the API client for data interaction.
        """
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout()

        # UI labels (French), page keys (must match MainWindow dictionary keys)
        buttons = [
            ("Prendre commande", "ORDER"),
            ("Gestion des stocks", "STOCK"),
            ("Gestion des articles", "ITEMS"),
            ("Gestion des accès", "ACCESS"),
            ("Historique", "HISTORY")
        ]

        # Create buttons dynamically
        for text, page_key in buttons:
            btn = QPushButton(text)
            # Link the button click to the navigation method
            btn.clicked.connect(lambda checked, pk=page_key: self.main_window.go_to(pk))
            layout.addWidget(btn)

        self.setLayout(layout)