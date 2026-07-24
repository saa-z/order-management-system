from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView


class HistoryPage(QWidget):
    def __init__(self, main_window, api_client):
        """
        Initialize the History Page.
        """
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        layout = QVBoxLayout()

        # Title
        layout.addWidget(QLabel("Historique des Commandes"))

        # Table to display order history
        self.table = QTableWidget(0, 4)  # 4 columns
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Total", "Statut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Buttons
        btn_refresh = QPushButton("Rafraîchir")
        btn_refresh.clicked.connect(self.load_history)
        layout.addWidget(btn_refresh)

        btn_back = QPushButton("Retour au menu")
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        layout.addWidget(btn_back)

        self.setLayout(layout)

        # Load data initially
        self.load_history()

    def load_history(self):
        """Fetch orders from the API and display them in the table."""
        try:
            # Assuming your API has a method get_orders()
            # Replace 'get_orders()' with your actual endpoint function
            orders = self.api.get_orders()
            self.table.setRowCount(0)

            for order in orders:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(order.get('id', 'N/A'))))
                self.table.setItem(row, 1, QTableWidgetItem(str(order.get('date', 'N/A'))))
                self.table.setItem(row, 2, QTableWidgetItem(f"{order.get('total', 0)}€"))
                self.table.setItem(row, 3, QTableWidgetItem(str(order.get('status', 'N/A'))))

        except Exception as e:
            print(f"Could not load history: {e}")