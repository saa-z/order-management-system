from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                               QHeaderView, QInputDialog, QComboBox, QDialog)
from PySide6.QtCore import Qt
from views.order_type_dialog import OrderTypeDialog  # Import mis à jour avec le bon nom de fichier


class PosOrderPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.categories_data = {}
        self.cart_total = 0.0

        # Attributs de commande (SQLAlchemy)
        self.order_type = "eat in"
        self.table_number = None

        self.init_ui()
        self.refresh_data()

    def showEvent(self, event):
        """Déclenché automatiquement chaque fois que la vue devient visible."""
        super().showEvent(event)
        self.setup_new_order()

    def setup_new_order(self):
        """Affiche la Pop-up pour paramétrer la nouvelle commande."""
        dialog = OrderTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.order_type = dialog.order_type
            self.table_number = dialog.table_number

            # Mise à jour de l'affichage du mode sélectionné
            info_text = f"Mode : {self.order_type.upper()}"
            if self.table_number:
                info_text += f" | Table : {self.table_number}"
            self.order_info_label.setText(info_text)
        else:
            # Si annulation, retour au menu principal
            self.main_window.go_to("MENU")

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

        right_panel.addWidget(QLabel("Panier"))

        # Label d'informations de commande (Table / Type)
        self.order_info_label = QLabel("Mode : Non défini")
        self.order_info_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        right_panel.addWidget(self.order_info_label)

        self.cart_list = QTableWidget(0, 3)
        self.cart_list.setHorizontalHeaderLabels(["Article", "Qté", "Prix"])
        self.cart_list.setShowGrid(False)

        # Configuration des colonnes
        self.cart_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Double-clic pour éditer les commentaires
        self.cart_list.itemDoubleClicked.connect(self.edit_row_comment)

        self.cart_total_label = QLabel("Total: 0.00 €")
        self.cart_total_label.setStyleSheet("font-weight: bold; font-size: 20px;")

        right_panel.addWidget(self.cart_list)
        right_panel.addWidget(self.cart_total_label)

        right_panel.addWidget(QPushButton("Envoyer en cuisine"))
        right_panel.addWidget(QPushButton("Facturer"))
        right_panel.addWidget(QPushButton("Annuler"))

        # Assemblage final des layouts
        content_layout.addLayout(left_panel, stretch=1)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

    def refresh_data(self):
        try:
            # Chargement des catégories depuis l'API
            categories_list = self.api.get_categories()
            self.categories_data = {cat['nom']: cat['items'] for cat in categories_list}
            self.load_categories()

        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Could not load data: {e}")

    def add_to_cart(self, row, column):
        """Ajoute l'article sélectionné au panier."""
        item_data = self.items_table.item(row, 0).data(Qt.UserRole).copy()
        item_data['commentaire'] = None
        item_data['option_selectionnee'] = None

        options = item_data.get('options')
        liste_options = []

        if options:
            if isinstance(options, dict):
                liste_options = [nom for nom, stock in options.items() if stock > 0]
            elif isinstance(options, list):
                liste_options = options

        if liste_options:
            option_choisie, ok = QInputDialog.getItem(
                self,
                "Sélectionner une option",
                f"Quel parfum pour '{item_data['nom']}' ?",
                liste_options,
                0,
                False
            )

            if not ok:
                return

            item_data['option_selectionnee'] = option_choisie

        cart_row = self.cart_list.rowCount()
        self.cart_list.insertRow(cart_row)

        display_name = item_data['nom']
        if item_data['option_selectionnee']:
            display_name = f"{item_data['nom']} : {item_data['option_selectionnee']}"

        name_item = QTableWidgetItem(display_name)
        name_item.setData(Qt.UserRole, item_data)
        self.cart_list.setItem(cart_row, 0, name_item)

        combo = QComboBox()
        combo.addItems([str(i) for i in range(1, 21)])
        combo.currentIndexChanged.connect(self.update_total)
        self.cart_list.setCellWidget(cart_row, 1, combo)

        self.cart_list.setItem(cart_row, 2, QTableWidgetItem(f"{item_data['prix']:.2f}"))

        self.update_total()

    def update_total(self):
        """Recalcule le total de la commande."""
        new_total = 0.0
        for row in range(self.cart_list.rowCount()):
            price_item = self.cart_list.item(row, 2)
            if price_item:
                price = float(price_item.text())
                combo = self.cart_list.cellWidget(row, 1)
                qty = int(combo.currentText()) if combo else 1
                new_total += (price * qty)

        self.cart_total = new_total
        self.cart_total_label.setText(f"Total: {self.cart_total:.2f} €")

    def edit_row_comment(self, item):
        """Edite le commentaire d'une ligne du panier."""
        if item.tableWidget() != self.cart_list:
            return

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