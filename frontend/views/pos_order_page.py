from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                               QHeaderView, QComboBox, QDialog, QFrame,
                               QTimeEdit, QLineEdit, QSpinBox, QCheckBox,
                               QRadioButton, QButtonGroup, QScrollArea)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from collections import defaultdict
from datetime import datetime

from views.order_type_dialog import OrderTypeDialog
from views.option_picker_dialog import OptionPickerDialog


_BASE_NAMES = {"tomate", "crème fraîche"}


def _format_modifications_display(mods):
    if not mods:
        return ""
    parts = []
    for m in mods:
        t = m.get("modification_type", "")
        n = m.get("ingredient_name", "?")
        if t == "base_change":
            parts.append(f"base {n}")
        elif t == "remove":
            parts.append(f"−{n}")
        elif t == "add":
            parts.append(f"+{n}")
    return ", ".join(parts)


class CartEditDialog(QDialog):
    """Edit comment and ingredient modifications for an existing cart row."""

    def __init__(self, item_data, all_ingredients, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Modifier — {item_data.get('name', '')}")
        self.setMinimumWidth(420)

        item_ingr = item_data.get("ingredients") or []
        initial_mods = item_data.get("modifications") or []

        self._item_ingr = item_ingr
        self._all_ingr = all_ingredients
        self._current_base_id = None
        self._base_group = None
        self._removal_checks = {}
        self._supp_checks = {}

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 16, 20, 16)

        # Comment
        root.addWidget(QLabel("Commentaire :"))
        self._comment = QLineEdit(item_data.get("comment") or "")
        self._comment.setPlaceholderText("Notes pour la cuisine…")
        root.addWidget(self._comment)

        # Ingredient modifications (only if item has ingredients)
        if item_ingr:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            root.addWidget(sep)

            # Decode initial state
            initial_base_id = None
            initial_removed = set()
            initial_added = set()
            for m in initial_mods:
                t = m.get("modification_type")
                iid = m.get("ingredient_id")
                if t == "base_change":
                    initial_base_id = iid
                elif t == "remove":
                    initial_removed.add(iid)
                elif t == "add":
                    initial_added.add(iid)

            scroll_w = QWidget()
            sv = QVBoxLayout(scroll_w)
            sv.setSpacing(12)
            sv.setContentsMargins(0, 0, 0, 0)

            # Base toggle
            base_in_item = [i for i in item_ingr if i["name"].lower() in _BASE_NAMES]
            if base_in_item:
                self._current_base_id = base_in_item[0]["id"]
                lbl = QLabel("Base :")
                lbl.setObjectName("dialog-section")
                sv.addWidget(lbl)
                base_row = QHBoxLayout()
                self._base_group = QButtonGroup(self)
                all_bases = [i for i in all_ingredients if i["name"].lower() in _BASE_NAMES]
                for ing in all_bases:
                    rb = QRadioButton(ing["name"])
                    rb.setProperty("ing_id", ing["id"])
                    rb.setProperty("ing_name", ing["name"])
                    if initial_base_id is not None:
                        rb.setChecked(ing["id"] == initial_base_id)
                    else:
                        rb.setChecked(ing["id"] == self._current_base_id)
                    self._base_group.addButton(rb)
                    base_row.addWidget(rb)
                base_row.addStretch()
                sv.addLayout(base_row)

            # Retraits
            non_base = [i for i in item_ingr if i["name"].lower() not in _BASE_NAMES]
            if non_base:
                lbl2 = QLabel("Retraits (décochez pour retirer) :")
                lbl2.setObjectName("dialog-section")
                sv.addWidget(lbl2)
                grid = QHBoxLayout()
                c1 = QVBoxLayout(); c1.setSpacing(4)
                c2 = QVBoxLayout(); c2.setSpacing(4)
                for idx, ingr in enumerate(non_base):
                    cb = QCheckBox(ingr["name"])
                    cb.setChecked(ingr["id"] not in initial_removed)
                    self._removal_checks[ingr["id"]] = {"cb": cb, "name": ingr["name"]}
                    (c1 if idx % 2 == 0 else c2).addWidget(cb)
                grid.addLayout(c1); grid.addLayout(c2); grid.addStretch()
                sv.addLayout(grid)

            # Suppléments
            item_ingr_ids = {i["id"] for i in item_ingr}
            supp_ingr = [
                i for i in all_ingredients
                if i["id"] not in item_ingr_ids and i["name"].lower() not in _BASE_NAMES
            ]
            if supp_ingr:
                lbl3 = QLabel("Supplément +1€ (cochez pour ajouter) :")
                lbl3.setObjectName("dialog-section")
                sv.addWidget(lbl3)
                sgrid = QHBoxLayout()
                sc1 = QVBoxLayout(); sc1.setSpacing(4)
                sc2 = QVBoxLayout(); sc2.setSpacing(4)
                for idx, ingr in enumerate(supp_ingr):
                    cb = QCheckBox(f"{ingr['name']} (+1€)")
                    cb.setChecked(ingr["id"] in initial_added)
                    self._supp_checks[ingr["id"]] = {"cb": cb, "name": ingr["name"]}
                    (sc1 if idx % 2 == 0 else sc2).addWidget(cb)
                sgrid.addLayout(sc1); sgrid.addLayout(sc2); sgrid.addStretch()
                sv.addLayout(sgrid)

            sv.addStretch()
            scroll = QScrollArea()
            scroll.setWidget(scroll_w)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setMaximumHeight(360)
            root.addWidget(scroll)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btn_ok = QPushButton("Valider")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        root.addLayout(btns)

    def get_comment(self):
        t = self._comment.text().strip()
        return t if t else None

    def get_modifications(self):
        mods = []
        if self._base_group and self._current_base_id is not None:
            checked = self._base_group.checkedButton()
            if checked:
                new_id = checked.property("ing_id")
                if new_id != self._current_base_id:
                    mods.append({
                        "ingredient_id": new_id,
                        "modification_type": "base_change",
                        "ingredient_name": checked.property("ing_name"),
                    })
        for iid, info in self._removal_checks.items():
            if not info["cb"].isChecked():
                mods.append({"ingredient_id": iid, "modification_type": "remove", "ingredient_name": info["name"]})
        for iid, info in self._supp_checks.items():
            if info["cb"].isChecked():
                mods.append({"ingredient_id": iid, "modification_type": "add", "ingredient_name": info["name"]})
        return mods if mods else None


class PosOrderPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self.categories_data = {}
        self.cart_total = 0.0

        self.order_type = "eat_in"
        self.seating_location = None
        self._current_order = None
        self._all_ingredients = []

        self.init_ui()
        self.refresh_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.setup_new_order()

    def setup_new_order(self):
        dialog = OrderTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.order_type = dialog.order_type
            self.seating_location = dialog.seating_location

            type_labels = {"eat_in": "SUR PLACE", "take_away": "A EMPORTER"}
            seating_labels = {"indoor": "Salle", "outdoor": "Terrasse"}
            info_text = f"Mode : {type_labels.get(self.order_type, self.order_type)}"
            if self.seating_location:
                info_text += f"  |  {seating_labels.get(self.seating_location, self.seating_location)}"
            self.order_info_label.setText(info_text)

            is_eat_in = self.order_type == "eat_in"
            is_take_away = self.order_type == "take_away"
            self.eatin_widget.setVisible(is_eat_in)
            self.takeaway_widget.setVisible(is_take_away)
            if is_eat_in:
                self.spin_table.setValue(1)
                self.spin_covers.setValue(1)
            if is_take_away:
                self.pickup_time_edit.setTime(QTime.currentTime().addSecs(1800))
                self.customer_name_edit.clear()
                self.customer_phone_edit.clear()
        else:
            self.main_window.go_to("MENU")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        title = QLabel("Prise de commande")
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
        content_layout.setSpacing(16)

        left_panel = QHBoxLayout()
        left_panel.setSpacing(10)

        self.cat_table = QTableWidget(0, 1)
        self.cat_table.setObjectName("cat-table")
        self.cat_table.horizontalHeader().hide()
        self.cat_table.verticalHeader().hide()
        self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cat_table.setShowGrid(False)
        self.cat_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cat_table.setSelectionMode(QTableWidget.SingleSelection)
        self.cat_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cat_table.setFocusPolicy(Qt.NoFocus)
        self.cat_table.itemClicked.connect(self.on_category_selected)
        left_panel.addWidget(self.cat_table, stretch=1)

        self.items_table = QTableWidget(0, 3)
        self.items_table.setObjectName("items-table")
        self.items_table.setHorizontalHeaderLabels(["Article", "Stock", "Prix"])
        self.items_table.verticalHeader().hide()
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.setShowGrid(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setFocusPolicy(Qt.NoFocus)
        self.items_table.cellClicked.connect(self.add_to_cart)
        left_panel.addWidget(self.items_table, stretch=3)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        cart_header = QLabel("Panier")
        cart_header.setObjectName("section-header")
        right_panel.addWidget(cart_header)

        self.order_info_label = QLabel("Mode : Non defini")
        self.order_info_label.setObjectName("order-info")
        right_panel.addWidget(self.order_info_label)

        takeaway_layout = QVBoxLayout()
        takeaway_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addWidget(QLabel("Nom :"))
        self.customer_name_edit = QLineEdit()
        self.customer_name_edit.setPlaceholderText("Nom du client")
        self.customer_name_edit.setMinimumHeight(30)
        row1.addWidget(self.customer_name_edit)
        row1.addWidget(QLabel("Tel :"))
        self.customer_phone_edit = QLineEdit()
        self.customer_phone_edit.setPlaceholderText("Telephone")
        self.customer_phone_edit.setMinimumHeight(30)
        row1.addWidget(self.customer_phone_edit)
        takeaway_layout.addLayout(row1)

        row2_pickup = QHBoxLayout()
        row2_pickup.setSpacing(6)
        row2_pickup.addWidget(QLabel("Retrait :"))
        self.pickup_time_edit = QTimeEdit()
        self.pickup_time_edit.setDisplayFormat("HH:mm")
        self.pickup_time_edit.setTime(QTime.currentTime().addSecs(1800))
        self.pickup_time_edit.setMinimumHeight(30)
        row2_pickup.addWidget(self.pickup_time_edit)
        row2_pickup.addStretch()
        takeaway_layout.addLayout(row2_pickup)

        self.takeaway_widget = QWidget()
        self.takeaway_widget.setLayout(takeaway_layout)
        self.takeaway_widget.setVisible(False)
        right_panel.addWidget(self.takeaway_widget)

        eatin_layout = QHBoxLayout()
        eatin_layout.setSpacing(8)
        eatin_layout.addWidget(QLabel("Table :"))
        self.spin_table = QSpinBox()
        self.spin_table.setRange(1, 200)
        self.spin_table.setMinimumHeight(30)
        eatin_layout.addWidget(self.spin_table)
        eatin_layout.addWidget(QLabel("Couverts :"))
        self.spin_covers = QSpinBox()
        self.spin_covers.setRange(1, 50)
        self.spin_covers.setMinimumHeight(30)
        eatin_layout.addWidget(self.spin_covers)
        eatin_layout.addStretch()

        self.eatin_widget = QWidget()
        self.eatin_widget.setLayout(eatin_layout)
        self.eatin_widget.setVisible(False)
        right_panel.addWidget(self.eatin_widget)

        self.cart_list = QTableWidget(0, 4)
        self.cart_list.setObjectName("cart-table")
        self.cart_list.setHorizontalHeaderLabels(["Article", "Qté", "Prix", ""])
        self.cart_list.verticalHeader().hide()
        self.cart_list.verticalHeader().setDefaultSectionSize(38)
        self.cart_list.setShowGrid(False)
        self.cart_list.setAlternatingRowColors(True)
        self.cart_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cart_list.setColumnWidth(1, 82)
        self.cart_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.cart_list.setColumnWidth(3, 66)
        right_panel.addWidget(self.cart_list)

        self.cart_total_label = QLabel("Total : 0.00 €")
        self.cart_total_label.setObjectName("cart-total")
        self.cart_total_label.setAlignment(Qt.AlignRight)
        right_panel.addWidget(self.cart_total_label)

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_kitchen = QPushButton("Envoyer en cuisine")
        self.btn_kitchen.setObjectName("btn-kitchen")
        self.btn_kitchen.setCursor(Qt.PointingHandCursor)
        self.btn_kitchen.clicked.connect(self.send_to_kitchen)
        actions_layout.addWidget(self.btn_kitchen)

        self.btn_invoice = QPushButton("Facturer")
        self.btn_invoice.setObjectName("btn-invoice")
        self.btn_invoice.setCursor(Qt.PointingHandCursor)
        self.btn_invoice.clicked.connect(self._invoice_order)
        self.btn_invoice.setVisible(False)
        actions_layout.addWidget(self.btn_invoice)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.btn_new_order = QPushButton("Nouvelle commande")
        self.btn_new_order.setObjectName("btn-secondary")
        self.btn_new_order.setCursor(Qt.PointingHandCursor)
        self.btn_new_order.clicked.connect(self._reset_order)
        self.btn_new_order.setVisible(False)
        row2.addWidget(self.btn_new_order)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("btn-cancel-order")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._cancel_order)
        row2.addWidget(self.btn_cancel)

        actions_layout.addLayout(row2)
        right_panel.addLayout(actions_layout)

        content_layout.addLayout(left_panel, stretch=3)
        content_layout.addLayout(right_panel, stretch=2)
        main_layout.addLayout(content_layout)

    def refresh_data(self):
        try:
            categories_list = self.api.get_categories()
            self.categories_data = {cat["name"]: cat["items"] for cat in categories_list}
            self._all_ingredients = self.api.get_ingredients()
            self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Erreur API", f"Impossible de charger les donnees : {e}")

    def _format_selected_options_display(self, selected_options):
        if not selected_options:
            return ""
        return ", ".join(f"{o['name']} x{o['quantity']}" for o in selected_options)

    def add_to_cart(self, row, column):
        item_data = self.items_table.item(row, 0).data(Qt.UserRole).copy()

        if not item_data.get("is_in_stock", True):
            QMessageBox.warning(self, "Rupture de stock", f"« {item_data['name']} » n'est plus disponible.")
            return

        item_data["comment"] = None
        item_data["selected_options"] = None
        item_data["modifications"] = None

        options = item_data.get("options", [])

        if options:
            available_options = [o for o in options if o["stock_quantity"] is None or o["stock_quantity"] > 0]
            if not available_options:
                QMessageBox.warning(self, "Rupture", f"Toutes les options de « {item_data['name']} » sont en rupture.")
                return

            dialog = OptionPickerDialog(item_data["name"], available_options, self)
            if dialog.exec() != QDialog.Accepted:
                return

            selected = dialog.get_selected_options()
            if not selected:
                QMessageBox.warning(self, "Aucune selection", "Veuillez selectionner au moins une option.")
                return

            item_data["selected_options"] = selected
            qty = dialog.get_total_quantity()
        else:
            qty = 1

        # Clé de correspondance : même article + mêmes options
        def _options_key(opts):
            if not opts:
                return ()
            return tuple(sorted((o["item_option_id"], o["quantity"]) for o in opts))

        new_key = (item_data["id"], _options_key(item_data.get("selected_options")))
        for r in range(self.cart_list.rowCount()):
            existing = self.cart_list.item(r, 0).data(Qt.UserRole)
            if existing and not existing.get("comment") and not existing.get("modifications"):
                exist_key = (existing["id"], _options_key(existing.get("selected_options")))
                if exist_key == new_key:
                    spin = self.cart_list.cellWidget(r, 1)
                    if spin:
                        spin.setValue(spin.value() + qty)
                    self.update_total()
                    return

        cart_row = self.cart_list.rowCount()
        self.cart_list.insertRow(cart_row)

        display_name = item_data["name"]
        if item_data["selected_options"]:
            details = self._format_selected_options_display(item_data["selected_options"])
            display_name = f"{item_data['name']} ({details})"

        name_item = QTableWidgetItem(display_name)
        name_item.setData(Qt.UserRole, item_data)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.cart_list.setItem(cart_row, 0, name_item)

        spin = QSpinBox()
        spin.setObjectName("cart-qty")
        spin.setRange(1, 99)
        spin.setValue(qty)
        spin.setAlignment(Qt.AlignCenter)
        spin.valueChanged.connect(self.update_total)
        self.cart_list.setCellWidget(cart_row, 1, spin)

        price_item = QTableWidgetItem(f"{float(item_data['price']):.2f}")
        price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
        price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cart_list.setItem(cart_row, 2, price_item)

        self.cart_list.setCellWidget(cart_row, 3, self._make_cart_action_widget())

        self.update_total()

    def update_total(self):
        new_total = 0.0
        for row in range(self.cart_list.rowCount()):
            price_item = self.cart_list.item(row, 2)
            spin = self.cart_list.cellWidget(row, 1)
            if price_item and spin:
                new_total += float(price_item.text()) * spin.value()
        self.cart_total = new_total
        self.cart_total_label.setText(f"Total : {self.cart_total:.2f} €")

    def load_categories(self):
        self.cat_table.setRowCount(0)
        for category_name in self.categories_data.keys():
            row = self.cat_table.rowCount()
            self.cat_table.insertRow(row)
            cat_item = QTableWidgetItem(category_name)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            self.cat_table.setItem(row, 0, cat_item)

    def on_category_selected(self, item):
        self.load_items(item.text())

    def load_items(self, category_name):
        self.items_table.setRowCount(0)
        items = self.categories_data.get(category_name, [])
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.UserRole, item)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 0, name_item)

            stock_val = item.get("stock_quantity")
            stock_text = str(stock_val) if stock_val is not None else ""
            stock_item = QTableWidgetItem(stock_text)
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            stock_item.setTextAlignment(Qt.AlignCenter)
            if stock_val is not None and stock_val <= 3:
                stock_item.setForeground(Qt.red)
            self.items_table.setItem(row, 1, stock_item)

            price_item = QTableWidgetItem(f"{float(item['price']):.2f} €")
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 2, price_item)

    def _make_cart_action_widget(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 0, 2, 0)
        h.setSpacing(2)

        def get_row():
            for r in range(self.cart_list.rowCount()):
                if self.cart_list.cellWidget(r, 3) is w:
                    return r
            return -1

        btn_edit = QPushButton("✏")
        btn_edit.setObjectName("btn-cart-edit")
        btn_edit.setFixedSize(28, 28)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setToolTip("Modifier")
        btn_edit.clicked.connect(lambda: self._edit_cart_row(get_row()))
        h.addWidget(btn_edit)

        btn_rm = QPushButton("✕")
        btn_rm.setObjectName("btn-cart-remove")
        btn_rm.setFixedSize(28, 28)
        btn_rm.setCursor(Qt.PointingHandCursor)
        btn_rm.setToolTip("Retirer")
        btn_rm.clicked.connect(lambda: self._remove_cart_row(get_row()))
        h.addWidget(btn_rm)

        return w

    def _edit_cart_row(self, row):
        if row < 0:
            return
        name_item = self.cart_list.item(row, 0)
        if not name_item:
            return
        item_data = name_item.data(Qt.UserRole)

        dlg = CartEditDialog(item_data, self._all_ingredients, self)
        if dlg.exec() != QDialog.Accepted:
            return

        item_data["comment"] = dlg.get_comment()
        item_data["modifications"] = dlg.get_modifications()

        display_name = item_data["name"]
        if item_data.get("selected_options"):
            details = self._format_selected_options_display(item_data["selected_options"])
            display_name = f"{item_data['name']} ({details})"
        if item_data.get("modifications"):
            display_name += f" [{_format_modifications_display(item_data['modifications'])}]"
        if item_data.get("comment"):
            display_name += f" [{item_data['comment']}]"

        name_item.setText(display_name)
        name_item.setData(Qt.UserRole, item_data)

        supp_cost = sum(1.0 for m in (item_data.get("modifications") or []) if m.get("modification_type") == "add")
        unit_price = float(item_data["price"]) + supp_cost
        price_item = self.cart_list.item(row, 2)
        if price_item:
            price_item.setText(f"{unit_price:.2f}")

        self.update_total()

    def _remove_cart_row(self, row):
        if row >= 0:
            self.cart_list.removeRow(row)
            self.update_total()

    def _build_order_payload(self):
        order_items = []
        items_to_print = []

        for row in range(self.cart_list.rowCount()):
            item_widget = self.cart_list.item(row, 0)
            item_data = item_widget.data(Qt.UserRole)

            spin = self.cart_list.cellWidget(row, 1)
            qty = spin.value() if spin else 1

            api_selected_options = None
            if item_data.get("selected_options"):
                api_selected_options = [
                    {"item_option_id": o["item_option_id"], "quantity": o["quantity"]}
                    for o in item_data["selected_options"]
                ]

            api_modifications = None
            if item_data.get("modifications"):
                api_modifications = [
                    {"ingredient_id": m["ingredient_id"], "modification_type": m["modification_type"]}
                    for m in item_data["modifications"]
                ]

            order_items.append({
                "item_id": item_data["id"],
                "quantity": qty,
                "selected_options": api_selected_options,
                "modifications": api_modifications,
                "comment": item_data.get("comment"),
            })

            cat_name = "AUTRES"
            for c_name, items in self.categories_data.items():
                if any(it.get("name") == item_data.get("name") for it in items):
                    cat_name = c_name
                    break

            items_to_print.append({
                "name": item_data.get("name"),
                "selected_options": item_data.get("selected_options"),
                "modifications": item_data.get("modifications"),
                "comment": item_data.get("comment"),
                "quantity": qty,
                "category": cat_name
            })

        pickup_time = None
        customer_name = None
        customer_phone = None
        if self.order_type == "take_away":
            pickup_time = self.pickup_time_edit.time().toString("HH:mm")
            customer_name = self.customer_name_edit.text().strip() or None
            customer_phone = self.customer_phone_edit.text().strip() or None

        table_number = None
        covers = None
        if self.order_type == "eat_in":
            table_number = self.spin_table.value()
            covers = self.spin_covers.value()

        order_payload = {
            "table_number": table_number,
            "covers": covers,
            "seating_location": self.seating_location,
            "order_type": self.order_type,
            "pickup_time": pickup_time,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "items": order_items,
        }

        return order_payload, items_to_print

    def send_to_kitchen(self):
        if self.cart_list.rowCount() == 0:
            QMessageBox.warning(self, "Panier vide", "Le panier est vide. Impossible d'envoyer en cuisine.")
            return

        order_payload, items_to_print = self._build_order_payload()

        result = self.api.create_order(order_payload)
        if not result:
            QMessageBox.critical(self, "Erreur", "Impossible de creer la commande.")
            return

        self._current_order = result

        categorized_items = defaultdict(list)
        for item in items_to_print:
            cat_name = item.get("category", "Autres").upper()
            categorized_items[cat_name].append(item)

        def get_category_priority(cat_name):
            name_lower = cat_name.lower()
            end_keywords = ["boisson", "alcool", "dessert"]
            if any(kw in name_lower for kw in end_keywords):
                return 1
            return 0

        sorted_categories = sorted(categorized_items.keys(), key=get_category_priority)

        self._set_post_order_mode(True)
        self.print_kitchen_ticket(result, categorized_items, sorted_categories)

    def _set_post_order_mode(self, active: bool):
        self.btn_kitchen.setVisible(not active)
        self.btn_invoice.setVisible(active)
        self.btn_new_order.setVisible(active)
        self.cat_table.setEnabled(not active)
        self.items_table.setEnabled(not active)
        self.cart_list.setEnabled(not active)

    def _reset_order(self):
        self._current_order = None
        self.cart_list.setRowCount(0)
        self.update_total()
        self._set_post_order_mode(False)
        self.setup_new_order()

    def _cancel_order(self):
        if self._current_order:
            if not QMessageBox.question(
                self, "Annuler la commande",
                f"Annuler la commande #{self._current_order['id']} ?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes:
                return
            self.api.update_order_status(self._current_order["id"], "cancelled")
        self._current_order = None
        self.cart_list.setRowCount(0)
        self.update_total()
        self._set_post_order_mode(False)
        self.setup_new_order()

    def _invoice_order(self):
        if not self._current_order:
            return
        order_id = self._current_order["id"]
        self.api.update_order_status(order_id, "paid")

        order = self._current_order
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        type_labels = {"eat_in": "SUR PLACE", "take_away": "A EMPORTER"}
        seating_labels = {"indoor": "Salle", "outdoor": "Terrasse"}

        info_lines = [
            f"<b>Commande :</b> #{order_id}",
            f"<b>Type :</b> {type_labels.get(order.get('order_type', ''), '')}",
        ]
        if order.get("seating_location"):
            info_lines.append(f"<b>Emplacement :</b> {seating_labels.get(order['seating_location'], '')}")
        if order.get("table_number"):
            info_lines.append(f"<b>Table :</b> {order['table_number']}")
        if order.get("covers"):
            info_lines.append(f"<b>Couverts :</b> {order['covers']}")
        if order.get("pickup_time"):
            info_lines.append(f"<b>Retrait :</b> {order['pickup_time']}")
        if order.get("customer_name"):
            info_lines.append(f"<b>Client :</b> {order['customer_name']}")
        if order.get("customer_phone"):
            info_lines.append(f"<b>Tel :</b> {order['customer_phone']}")
        info_html = "<br>".join(info_lines)

        rows_html = ""
        items_data = order.get("items", [])
        categorized: dict = {}
        for it in items_data:
            cat = "AUTRES"
            name = it.get("item_name_snapshot", "")
            for c_name, c_items in self.categories_data.items():
                if any(ci.get("name") == name for ci in c_items):
                    cat = c_name.upper()
                    break
            categorized.setdefault(cat, []).append(it)

        total = 0.0
        for cat, c_items in categorized.items():
            rows_html += f'<tr><td colspan="3" class="cat">{cat}</td></tr>'
            for it in c_items:
                name = it.get("item_name_snapshot", "")
                opts = it.get("selected_options", [])
                if opts:
                    opts_str = ", ".join(o.get("option_name_snapshot", "") for o in opts)
                    name += f" <span class='opt'>({opts_str})</span>"
                qty = it.get("quantity", 1)
                up = float(it.get("unit_price") or 0)
                supp = sum(
                    float(m.get("unit_price") or 0)
                    for m in (it.get("modifications") or [])
                    if m.get("modification_type") == "add"
                )
                line = qty * (up + supp)
                total += line
                rows_html += f'<tr><td>{name}</td><td class="r">{qty}</td><td class="r">{line:.2f} €</td></tr>'

        html = f"""<html><head><style>
            body {{ font-family: Arial, sans-serif; font-size: 8pt; color: #000; margin: 0; padding: 0; }}
            .receipt {{ max-width: 72mm; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 4px; padding-bottom: 3px; border-bottom: 2px solid #000; }}
            .header h2 {{ font-size: 12pt; margin: 0; letter-spacing: 1px; }}
            .header p {{ font-size: 7pt; margin: 1px 0 0 0; }}
            .info {{ font-size: 7pt; padding: 2px 0; border-bottom: 1px solid #000; margin-bottom: 3px; line-height: 1.3; }}
            .date {{ font-size: 7pt; text-align: right; margin-bottom: 2px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .cat {{ font-weight: bold; font-size: 7pt; text-transform: uppercase; padding: 2px 3px; border-top: 1px solid #000; }}
            td {{ padding: 1px 3px; font-size: 8pt; line-height: 1.2; }}
            .r {{ text-align: right; white-space: nowrap; }}
            .opt {{ font-size: 6pt; }}
            .total {{ border-top: 2px solid #000; margin-top: 4px; padding-top: 3px; text-align: right; font-size: 11pt; font-weight: bold; }}
            .footer {{ text-align: center; font-size: 7pt; margin-top: 6px; padding-top: 3px; border-top: 1px dashed #000; }}
        </style></head><body>
        <div class="receipt">
            <div class="header"><h2>SAN GIORGIO</h2><p>Pizzeria - Restaurant Italien</p></div>
            <div class="date">{now}</div>
            <div class="info">{info_html}</div>
            <table>{rows_html}</table>
            <div class="total">TOTAL : {total:.2f} €</div>
            <div class="footer">Merci de votre visite !<br>A bientot chez San Giorgio</div>
        </div></body></html>"""

        self._print_html(html)
        self._reset_order()

    def _print_html(self, html):
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() != QDialog.Accepted:
            return False
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
        return True

    def _get_kitchen_info(self, order_id):
        type_labels = {"eat_in": "SUR PLACE", "take_away": "A EMPORTER"}
        seating_labels = {"indoor": "Salle", "outdoor": "Terrasse"}
        now = datetime.now().strftime("%H:%M")

        header = f"<b>#{order_id}</b>"
        if self.order_type == "eat_in":
            header += f" &nbsp; Table {self.spin_table.value()}"

        lines = [
            f"<div style='font-size:10pt;text-align:right;'>{now}</div>",
            f"<div style='font-size:11pt;'>{header}</div>",
            f"<div>{type_labels.get(self.order_type, self.order_type)}</div>",
        ]
        if self.seating_location:
            lines.append(f"<div>{seating_labels.get(self.seating_location, '')}</div>")
        if self.order_type == "take_away":
            pt = self.pickup_time_edit.time().toString("HH:mm")
            lines.append(f"<div><b>Retrait : {pt}</b></div>")
            name = self.customer_name_edit.text().strip()
            if name:
                lines.append(f"<div>{name}</div>")
        return "\n".join(lines)

    def print_kitchen_ticket(self, result, categorized_items, sorted_categories):
        order_id = result.get("id", "")
        info_html = self._get_kitchen_info(order_id)

        rows_html = ""
        for cat in sorted_categories:
            total_qty = sum(item["quantity"] for item in categorized_items[cat])
            rows_html += f'<tr><td colspan="2" class="cat">{cat} ({total_qty})</td></tr>'

            for item in categorized_items[cat]:
                details = f"<b>{item['name']}</b>"
                if item.get("selected_options"):
                    opts = self._format_selected_options_display(item["selected_options"])
                    details += f"<br><span class='opt'>{opts}</span>"
                if item.get("modifications"):
                    for mod in item["modifications"]:
                        t = mod.get("modification_type", "")
                        n = mod.get("ingredient_name", "?")
                        if t == "base_change":
                            details += f"<br><span class='mod-base'>Base : {n}</span>"
                        elif t == "remove":
                            details += f"<br><span class='mod-rm'>Retrait : {n}</span>"
                        elif t == "add":
                            details += f"<br><span class='mod-add'>Supplément : {n}</span>"
                if item.get("comment"):
                    details += f"<br><i class='cmt'>{item['comment']}</i>"

                rows_html += f'<tr><td class="qty">x{item["quantity"]}</td><td>{details}</td></tr>'

        html = f"""<html><head><style>
            body {{ font-family: Arial, sans-serif; font-size: 9pt; color: #000; margin: 0; padding: 0; }}
            .receipt {{ max-width: 72mm; margin: 0 auto; }}
            h2 {{ text-align: center; font-size: 12pt; margin: 0 0 3px 0; padding-bottom: 3px; border-bottom: 2px solid #000; }}
            .info {{ font-size: 8pt; padding: 3px 0; border-bottom: 1px solid #000; margin-bottom: 3px; line-height: 1.3; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .cat {{ font-weight: bold; font-size: 8pt; text-transform: uppercase; padding: 2px 3px; border-top: 1px solid #000; border-bottom: 1px dashed #000; }}
            td {{ padding: 2px 3px; vertical-align: top; font-size: 9pt; line-height: 1.2; }}
            .qty {{ font-weight: bold; font-size: 11pt; width: 15%; text-align: center; }}
            .opt {{ font-size: 7pt; }}
            .cmt {{ font-size: 7pt; color: #444; }}
            .mod-base {{ font-size: 7pt; font-style: italic; color: #555; }}
            .mod-rm {{ font-size: 7pt; color: #c00; font-weight: bold; }}
            .mod-add {{ font-size: 7pt; color: #080; font-weight: bold; }}
        </style></head><body>
        <div class="receipt">
            <h2>BON DE CUISINE</h2>
            <div class="info">{info_html}</div>
            <table>{rows_html}</table>
        </div>
        </body></html>"""

        if self._print_html(html):
            QMessageBox.information(self, "Cuisine", "Commande envoyee en cuisine avec succes !")
