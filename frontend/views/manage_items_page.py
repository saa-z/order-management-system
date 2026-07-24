from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel


class ManageItemsPage(QWidget):
    def __init__(self, main_window, api_client):
        """
        Initialize the Items Management Page.
        :param main_window: Reference to the MainWindow for navigation.
        :param api_client: Reference to the API client for data interaction.
        """
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Gestion Articles & Catégories"))

        # Back button
        btn_back = QPushButton("Retour au menu")
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        layout.addWidget(btn_back)

        self.setLayout(layout)