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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("Gestion des stocks")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)
        main_layout.addLayout(top_bar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        self.category_table = QTreeWidget()
        self.category_table.setHeaderHidden(True)
        self.category_table.itemClicked.connect(self.handle_category_selection)
        content_layout.addWidget(self.category_table, stretch=1)

        self.items_tree = QTreeWidget()
        self.items_tree.setColumnCount(2)
        self.items_tree.setHeaderLabels(["Article", "Stock Qte"])
        self.items_tree.setAlternatingRowColors(True)
        self.items_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        content_layout.addWidget(self.items_tree, stretch=3)

        main_layout.addLayout(content_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setObjectName("btn-secondary")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.fetch_data)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-danger")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.cancel_changes)

        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("btn-success")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_changes)

        button_layout.addWidget(btn_refresh)
        button_layout.addWidget(btn_cancel)
        button_layout.addStretch()
        button_layout.addWidget(btn_save)

        main_layout.addLayout(button_layout)

    def fetch_data(self):
        try:
            categories_list = self.api.get_categories()
            self.categories_data = {cat["name"]: cat["items"] for cat in categories_list}

            self.category_table.clear()

            for category_name in self.categories_data.keys():
                item = QTreeWidgetItem([category_name])
                self.category_table.addTopLevelItem(item)

            if self.current_category:
                self.restore_selection()
            else:
                self.items_tree.clear()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les stocks : {e}")

    def handle_category_selection(self, item, column):
        self.current_category = item.text(0)
        self.populate_items(self.current_category)

    def restore_selection(self):
        matches = self.category_table.findItems(self.current_category, Qt.MatchExactly)
        if matches:
            self.category_table.setCurrentItem(matches[0])
            self.populate_items(self.current_category)
        else:
            self.current_category = None
            self.items_tree.clear()

    def populate_items(self, category_name):
        self.items_tree.clear()
        items = self.categories_data.get(category_name, [])

        for item_data in items:
            options = item_data.get("options")

            parent_item = QTreeWidgetItem([item_data["name"]])
            self.items_tree.addTopLevelItem(parent_item)

            if options and isinstance(options, dict):
                parent_item.setExpanded(True)

                for option_name, option_stock in options.items():
                    child_item = QTreeWidgetItem([option_name])
                    parent_item.addChild(child_item)

                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.addItems([str(i) for i in range(101)])
                    combo.setCurrentText(str(option_stock))

                    combo.setProperty("item_id", item_data["id"])
                    combo.setProperty("is_option", True)
                    combo.setProperty("option_key", option_name)

                    self.items_tree.setItemWidget(child_item, 1, combo)
            else:
                combo = QComboBox()
                combo.setEditable(True)
                combo.addItems([str(i) for i in range(101)])
                combo.setCurrentText(str(item_data.get("stock_quantity", 0)))

                combo.setProperty("item_id", item_data["id"])
                combo.setProperty("is_option", False)

                self.items_tree.setItemWidget(parent_item, 1, combo)

    def save_changes(self):
        try:
            payloads = {}

            for i in range(self.items_tree.topLevelItemCount()):
                parent_item = self.items_tree.topLevelItem(i)

                combo = self.items_tree.itemWidget(parent_item, 1)
                if combo:
                    self._collect_combo_data(combo, payloads)

                for j in range(parent_item.childCount()):
                    child_item = parent_item.child(j)
                    child_combo = self.items_tree.itemWidget(child_item, 1)
                    if child_combo:
                        self._collect_combo_data(child_combo, payloads)

            for item_id, changes in payloads.items():
                if changes["options_dict"]:
                    self.api.update_stock_raw(item_id, {"options": changes["options_dict"]})
                elif changes["global_qty"] is not None:
                    self.api.update_item_stock(item_id, changes["global_qty"])

            QMessageBox.information(self, "Succes", "Stocks mis a jour avec succes.")
            self.fetch_data()

        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer des quantites numeriques valides.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur inattendue s'est produite : {e}")

    def _collect_combo_data(self, combo, payloads):
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
        self.fetch_data()
