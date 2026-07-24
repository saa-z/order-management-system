from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                               QHeaderView, QInputDialog, QComboBox)
from PySide6.QtCore import Qt


class PosOrderPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.categories_data = {}
        self.cart_total = 0.0
        self.current_order_id = 1  # Default ID

        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        """UI Construction."""
        main_layout = QVBoxLayout(self)

        # Top Bar
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        btn_back = QPushButton("Menu")
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        nav_layout.addWidget(btn_back)
        main_layout.addLayout(nav_layout)

        # Main container (Split 50/50)
        content_layout = QHBoxLayout()

        # --- LEFT PANEL (50%): Categories + Items ---
        left_panel = QHBoxLayout()

        self.cat_table = QTableWidget(0, 1)
        self.cat_table.horizontalHeader().hide()
        self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cat_table.setShowGrid(False)
        self.cat_table.itemClicked.connect(self.on_category_selected)
        left_panel.addWidget(self.cat_table, stretch=1)

        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["Article", "Stock", "Prix"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setShowGrid(False)
        self.items_table.cellClicked.connect(self.add_to_cart)
        left_panel.addWidget(self.items_table, stretch=3)

        # --- RIGHT PANEL (50%): Cart ---
        right_panel = QVBoxLayout()

        # Order ID label
        self.order_id_label = QLabel(f"Commande N° : {self.current_order_id}")
        self.order_id_label.setStyleSheet("font-size: 14px; color: #555; font-style: italic; margin-bottom: 5px;")

        self.cart_list = QTableWidget(0, 3)
        self.cart_list.setHorizontalHeaderLabels(["Article", "Qté", "Prix"])
        self.cart_list.setShowGrid(False)

        # Column configuration to occupy space
        self.cart_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Double-click to comment
        self.cart_list.itemDoubleClicked.connect(self.edit_row_comment)

        self.cart_total_label = QLabel("Total: 0.00 €")
        self.cart_total_label.setStyleSheet("font-weight: bold; font-size: 20px;")

        right_panel.addWidget(QLabel("Panier"))
        right_panel.addWidget(self.order_id_label)  # Add ID here
        right_panel.addWidget(self.cart_list)
        right_panel.addWidget(self.cart_total_label)

        right_panel.addWidget(QPushButton("Envoyer en cuisine"))
        right_panel.addWidget(QPushButton("Facturer"))
        right_panel.addWidget(QPushButton("Annuler"))

        # Final layout assembly
        content_layout.addLayout(left_panel, stretch=1)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

    def fetch_last_order_id(self):
        """Fetches the last order ID via the API to compute the next one."""
        try:
            # API call to get the last ID
            last_id = self.api.get_last_order_id()
            if last_id:
                self.current_order_id = int(last_id) + 1
            else:
                self.current_order_id = 1
        except Exception:
            # If API error, fall back to 1
            self.current_order_id = 1

        # Text update
        self.order_id_label.setText(f"Commande N° : {self.current_order_id}")

    def refresh_data(self):
        try:
            # 1. Load categories
            categories_list = self.api.get_categories()
            self.categories_data = {cat['nom']: cat['items'] for cat in categories_list}
            self.load_categories()

            # 2. Load last ID
            self.fetch_last_order_id()

        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Could not load data: {e}")

    def add_to_cart(self, row, column):
        """Adds the item to the cart with option selection if available."""
        # 1. Fetch raw data from the clicked item
        item_data = self.items_table.item(row, 0).data(Qt.UserRole).copy()
        item_data['commentaire'] = None

        # Initialize the selected option field
        item_data['option_selectionnee'] = None

        # 2. Check if the item has options available (e.g., ["Coca", "Orangina"])
        options = item_data.get('options')
        liste_options = []

        if options:
            if isinstance(options, dict):
                # On extrait les parfums qui ont encore du stock (> 0)
                liste_options = [nom for nom, stock in options.items() if stock > 0]
            elif isinstance(options, list):
                liste_options = options

        if liste_options:
            # Open input dialog with a dropdown list
            option_choisie, ok = QInputDialog.getItem(
                self,
                "Sélectionner une option",
                f"Quel parfum pour '{item_data['nom']}' ?",
                liste_options,  # On passe la liste nettoyée ici
                0,
                False
            )

            # If user cancels or closes the dialog, abort adding to cart
            if not ok:
                return

            # Save selected option inside item data dictionary
            item_data['option_selectionnee'] = option_choisie
        # 3. Insert row into cart
        cart_row = self.cart_list.rowCount()
        self.cart_list.insertRow(cart_row)

        # Col 0: Article Name (append option if selected)
        display_name = item_data['nom']
        if item_data['option_selectionnee']:
            display_name = f"{item_data['nom']} : {item_data['option_selectionnee']}"

        name_item = QTableWidgetItem(display_name)
        name_item.setData(Qt.UserRole, item_data)  # Store complete item_data dictionary inside
        self.cart_list.setItem(cart_row, 0, name_item)

        # Col 1: Quantity (ComboBox)
        combo = QComboBox()
        combo.addItems([str(i) for i in range(1, 21)])  # From 1 to 20
        combo.currentIndexChanged.connect(self.update_total)
        self.cart_list.setCellWidget(cart_row, 1, combo)

        # Col 2: Unit Price
        self.cart_list.setItem(cart_row, 2, QTableWidgetItem(f"{item_data['prix']:.2f}"))

        self.update_total()

    def update_total(self):
        """Recalculates total based on quantities."""
        new_total = 0.0
        for row in range(self.cart_list.rowCount()):
            # Fetch price
            price_item = self.cart_list.item(row, 2)
            if price_item:
                price = float(price_item.text())

                # Fetch quantity from ComboBox
                combo = self.cart_list.cellWidget(row, 1)
                qty = int(combo.currentText()) if combo else 1

                new_total += (price * qty)

        self.cart_total = new_total
        self.cart_total_label.setText(f"Total: {self.cart_total:.2f} €")

    def edit_row_comment(self, item):
        """Modifies row comment."""
        if item.tableWidget() != self.cart_list: return

        row = item.row()
        item_widget = self.cart_list.item(row, 0)
        item_data = item_widget.data(Qt.UserRole)

        text, ok = QInputDialog.getText(self, "Commentaire", "Entrez un commentaire :",
                                        text=item_data.get('commentaire') or "")
        if ok:
            item_data['commentaire'] = text
            display_text = f"{item_data['nom']} ({text})" if text else item_data['nom']
            item_widget.setText(display_text)
            item_widget.setData(Qt.UserRole, item_data)

    def load_categories(self):
        self.cat_table.setRowCount(0)
        for category_name in self.categories_data.keys():
            row = self.cat_table.rowCount()
            self.cat_table.insertRow(row)
            self.cat_table.setItem(row, 0, QTableWidgetItem(category_name))

    def on_category_selected(self, item):
        self.load_items(item.text())

    def load_items(self, category_name):
        self.items_table.setRowCount(0)
        items = self.categories_data.get(category_name, [])
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            name_item = QTableWidgetItem(item['nom'])
            name_item.setData(Qt.UserRole, item)
            self.items_table.setItem(row, 0, name_item)
            stock_val = item.get('quantite_en_stock')
            self.items_table.setItem(row, 1, QTableWidgetItem(str(stock_val) if stock_val is not None else ""))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{item['prix']:.2f} €"))