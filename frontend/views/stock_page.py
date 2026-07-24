from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QLabel, QMessageBox,
                               QHeaderView, QComboBox)
from PySide6.QtCore import Qt


class StockPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.categories_data = {}
        self.current_category = None

        self.init_ui()
        self.fetch_data()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Gestion des stocks (Arborescence)")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 1. Navigation Bar
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        btn_back = QPushButton("Menu")
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        nav_layout.addWidget(btn_back)
        main_layout.addLayout(nav_layout)

        # 2. Content Layout
        content_layout = QHBoxLayout()

        # Left Column: Categories (On garde le QTreeWidget ici aussi pour l'uniformité ou une table classique)
        self.category_table = QTreeWidget()
        self.category_table.setHeaderHidden(True)
        self.category_table.itemClicked.connect(self.handle_category_selection)
        content_layout.addWidget(self.category_table, stretch=1)

        # Right Column: Items (Remplacé par un QTreeWidget pour l'indentation)
        self.items_tree = QTreeWidget()
        self.items_tree.setColumnCount(2)
        self.items_tree.setHeaderLabels(["Article", "Stock Qté"])
        self.items_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        content_layout.addWidget(self.items_tree, stretch=3)

        main_layout.addLayout(content_layout)

        # 3. Bottom Action Buttons
        button_layout = QHBoxLayout()

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.fetch_data)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.cancel_changes)
        btn_cancel.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_changes)
        btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")

        button_layout.addWidget(btn_refresh)
        button_layout.addWidget(btn_cancel)
        button_layout.addStretch()
        button_layout.addWidget(btn_save)

        main_layout.addLayout(button_layout)

    def fetch_data(self):
        """Fetch categories and items from the API."""
        try:
            categories_list = self.api.get_categories()
            self.categories_data = {cat['nom']: cat['items'] for cat in categories_list}

            self.category_table.clear()

            for category_name in self.categories_data.keys():
                item = QTreeWidgetItem([category_name])
                self.category_table.addTopLevelItem(item)

            if self.current_category:
                self.restore_selection()
            else:
                self.items_tree.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load stocks: {e}")

    def handle_category_selection(self, item, column):
        """Handle category selection."""
        self.current_category = item.text(0)
        self.populate_items(self.current_category)

    def restore_selection(self):
        """Finds and re-selects the category after refresh."""
        matches = self.category_table.findItems(self.current_category, Qt.MatchExactly)
        if matches:
            self.category_table.setCurrentItem(matches[0])
            self.populate_items(self.current_category)
        else:
            self.current_category = None
            self.items_tree.clear()

    def populate_items(self, category_name):
        """Fill the tree with parents (items) and children (options)."""
        self.items_tree.clear()
        items = self.categories_data.get(category_name, [])

        for item_data in items:
            options = item_data.get('options')

            # 1. Créer la ligne parente (le produit)
            parent_item = QTreeWidgetItem([item_data['nom']])
            self.items_tree.addTopLevelItem(parent_item)

            # Cas A : Le produit possède des options (ex: Soda)
            if options and isinstance(options, dict):
                # On déplie automatiquement le parent pour voir les options
                parent_item.setExpanded(True)

                for option_name, option_stock in options.items():
                    # Créer la sous-ligne (Enfant), elle est automatiquement indentée
                    child_item = QTreeWidgetItem([option_name])
                    parent_item.addChild(child_item)

                    # Ajouter le menu déroulant de stock sur la ligne de l'option
                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.addItems([str(i) for i in range(101)])
                    combo.setCurrentText(str(option_stock))

                    # On lie les métadonnées au combo pour l'identification au moment de la sauvegarde
                    combo.setProperty("item_id", item_data['id'])
                    combo.setProperty("is_option", True)
                    combo.setProperty("option_key", option_name)

                    # Dans un QTreeWidget, on applique le widget à la colonne 1 de l'enfant
                    self.items_tree.setItemWidget(child_item, 1, combo)

            # Cas B : Produit simple sans options
            else:
                combo = QComboBox()
                combo.setEditable(True)
                combo.addItems([str(i) for i in range(101)])
                combo.setCurrentText(str(item_data.get('quantite_en_stock', 0)))

                combo.setProperty("item_id", item_data['id'])
                combo.setProperty("is_option", False)

                self.items_tree.setItemWidget(parent_item, 1, combo)

    def save_changes(self):
        """Scan the tree to extract combo boxes and save data."""
        try:
            payloads = {}

            # Pour parcourir un QTreeWidget, on doit boucler sur les éléments racines (TopLevel)
            for i in range(self.items_tree.topLevelItemCount()):
                parent_item = self.items_tree.topLevelItem(i)

                # Étape 1 : Vérifier si le parent lui-même a un combo widget (Produit simple)
                combo = self.items_tree.itemWidget(parent_item, 1)
                if combo:
                    self._collect_combo_data(combo, payloads)

                # Étape 2 : Parcourir ses enfants s'il en a (Produit à options)
                for j in range(parent_item.childCount()):
                    child_item = parent_item.child(j)
                    child_combo = self.items_tree.itemWidget(child_item, 1)
                    if child_combo:
                        self._collect_combo_data(child_combo, payloads)

            # Étape 3 : Envoi des requêtes filtrées à l'API
            for item_id, changes in payloads.items():
                if changes["options_dict"]:
                    payload = {"options": changes["options_dict"]}
                    self.api.update_stock_raw(item_id, payload)
                elif changes["global_qty"] is not None:
                    self.api.update_item_stock(item_id, changes["global_qty"])

            QMessageBox.information(self, "Success", "Stocks updated successfully.")
            self.fetch_data()

        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric quantities.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def _collect_combo_data(self, combo, payloads):
        """Helper to group combo data into structural payloads."""
        item_id = combo.property("item_id")
        is_option = combo.property("is_option")
        new_qty = int(combo.currentText())

        if item_id not in payloads:
            payloads[item_id] = {"global_qty": None, "options_dict": {}}

        if is_option:
            option_key = combo.property("option_key")
            payloads[item_id]["options_dict"][option_key] = new_qty
        else:
            payloads[item_id]["global_qty"] = new_qty

    def cancel_changes(self):
        """Discard changes by reloading data."""
        self.fetch_data()