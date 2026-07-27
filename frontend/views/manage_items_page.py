from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox,
    QAbstractItemView, QMessageBox, QComboBox, QSizePolicy,
    QScrollArea, QTabWidget, QFrame, QMenu,
)
import qtawesome as qta

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QBrush


_DELETED_FG = QColor("#A06060")


def _is_deleted(obj: dict) -> bool:
    return bool(obj.get("deleted_at"))


def _apply_deleted_style(item: QTableWidgetItem):
    item.setForeground(_DELETED_FG)
    f = item.font()
    f.setItalic(True)
    item.setFont(f)


class ToggleSwitch(QCheckBox):
    _TW, _TH, _THUMB = 44, 24, 18

    def __init__(self, label="", parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        tw, th, thumb = self._TW, self._TH, self._THUMB
        ty = (self.height() - th) // 2
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#B88647" if self.isChecked() else "#3A3530")))
        p.drawRoundedRect(0, ty, tw, th, th // 2, th // 2)
        tm = (th - thumb) // 2
        tx = tw - thumb - tm if self.isChecked() else tm
        p.setBrush(QBrush(QColor("#F5F1E6")))
        p.drawEllipse(tx, ty + tm, thumb, thumb)
        if self.text():
            p.setPen(QColor("#A09888"))
            p.drawText(tw + 8, 0, self.width() - tw - 8, self.height(),
                       Qt.AlignVCenter | Qt.AlignLeft, self.text())
        p.end()

    def sizeHint(self):
        extra = self.fontMetrics().horizontalAdvance(self.text()) + 8 if self.text() else 0
        return QSize(self._TW + extra, 28)

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)


class ManageItemsPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        self._show_deleted = False
        self._selected_cat_id = None
        self._selected_item_id = None
        self._selected_opt_id = None
        self._categories_data = []

        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_all()

    # ==========================================
    # UI CONSTRUCTION
    # ==========================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # Top bar
        top = QHBoxLayout()
        title = QLabel("Gestion des articles")
        title.setObjectName("page-title")
        top.addWidget(title)
        top.addStretch()

        self.toggle_deleted = ToggleSwitch("Afficher supprimes")
        self.toggle_deleted.toggled.connect(self._on_toggle_deleted)
        top.addWidget(self.toggle_deleted)

        self._more_menu = QMenu(self)
        self._more_menu.setStyleSheet("""
            QMenu {
                background-color: #2C2520;
                color: #F5F1E6;
                border: 1px solid #3E3530;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 7px 20px 7px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #B88647;
                color: #1A1510;
            }
        """)
        self._more_menu.addAction("Ajouter", self._top_add)
        self._more_menu.addAction("Modifier", self._top_edit)
        self._more_menu.addSeparator()
        self._more_menu.addAction("Supprimer", self._top_delete)

        btn_more = QPushButton()
        btn_more.setIcon(qta.icon("fa5s.ellipsis-h", color="#F5F1E6"))
        btn_more.setIconSize(QSize(16, 16))
        btn_more.setFixedSize(32, 32)
        btn_more.setCursor(Qt.PointingHandCursor)
        btn_more.setToolTip("Actions")
        btn_more.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #3E3530;"
            " border-radius: 4px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.08); }"
            "QPushButton:pressed { background: rgba(255,255,255,0.14); }"
        )
        btn_more.clicked.connect(
            lambda: self._more_menu.exec(btn_more.mapToGlobal(btn_more.rect().bottomLeft()))
        )
        top.addWidget(btn_more)

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top.addWidget(btn_back)

        root.addLayout(top)

        # 3-panel body
        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._make_cat_panel(), 1)
        body.addWidget(self._make_items_panel(), 1)
        body.addWidget(self._make_options_panel(), 1)
        root.addLayout(body)

    def _make_panel_header(self, label_text, on_add_clicked):
        h = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setObjectName("section-header")
        h.addWidget(lbl)
        btn = QPushButton("+ Ajouter")
        btn.setObjectName("btn-success")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(on_add_clicked)
        h.addWidget(btn)
        h.addStretch()
        return h

    def _make_table(self, col_labels, stretch_col=0):
        table = QTableWidget()
        table.setColumnCount(len(col_labels))
        table.setHorizontalHeaderLabels(col_labels)
        action_col = len(col_labels) - 1
        for i in range(len(col_labels)):
            if i == stretch_col:
                table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            elif i == action_col:
                table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
                table.setColumnWidth(i, 84)
            else:
                table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(44)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.setShowGrid(False)
        return table

    def _make_cat_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addLayout(self._make_panel_header("Categories", self._add_category))

        self.cat_table = self._make_table(["Nom", ""], stretch_col=0)
        self.cat_table.cellClicked.connect(self._on_cat_cell_clicked)
        v.addWidget(self.cat_table, 1)
        return w

    def _make_items_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addLayout(self._make_panel_header("Articles", self._add_item))

        self.items_table = self._make_table(["Nom", "Prix", "Dispo", ""], stretch_col=0)
        hdr = self.items_table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        self.items_table.setColumnWidth(1, 72)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed)
        self.items_table.setColumnWidth(2, 62)
        self.items_table.cellClicked.connect(self._on_item_cell_clicked)
        v.addWidget(self.items_table, 1)
        return w

    def _make_options_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addLayout(self._make_panel_header("Options", self._add_option))

        self.options_table = self._make_table(["Nom", "Stock", ""], stretch_col=0)
        hdr = self.options_table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        self.options_table.setColumnWidth(1, 72)
        self.options_table.cellClicked.connect(self._on_opt_cell_clicked)
        v.addWidget(self.options_table, 1)
        return w

    # ==========================================
    # ACTION CELL WIDGETS
    # ==========================================

    @staticmethod
    def _icon_btn(fa_name, tooltip, slot, color="#F5F1E6"):
        btn = QPushButton()
        btn.setIcon(qta.icon(fa_name, color=color))
        btn.setIconSize(QSize(16, 16))
        btn.setFixedWidth(30)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; padding: 0;"
            " min-height: 0; min-width: 0; }"
            "QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 4px; }"
        )
        btn.clicked.connect(slot)
        return btn

    def _make_action_widget(self, on_edit, on_action, is_deleted):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h = QHBoxLayout(w)
        h.setContentsMargins(8, 0, 8, 0)
        h.setSpacing(8)
        h.addWidget(self._icon_btn("fa5s.pen", "Modifier", on_edit, color="#F5F1E6"))
        if is_deleted:
            h.addWidget(self._icon_btn("fa5s.undo", "Restaurer", on_action, color="#F5F1E6"))
        else:
            h.addWidget(self._icon_btn("fa5s.trash-alt", "Supprimer", on_action, color="#C0392B"))
        return w

    def _make_cat_action_widget(self, cat):
        cat_id = cat["id"]
        is_del = _is_deleted(cat)
        return self._make_action_widget(
            on_edit=lambda: self._edit_category(cat_id),
            on_action=(lambda: self._restore_category(cat_id)) if is_del
                      else (lambda: self._delete_category(cat_id)),
            is_deleted=is_del,
        )

    def _make_item_action_widget(self, item):
        item_id = item["id"]
        is_del = _is_deleted(item)
        return self._make_action_widget(
            on_edit=lambda: self._edit_item(item_id),
            on_action=(lambda: self._restore_item(item_id)) if is_del
                      else (lambda: self._delete_item(item_id)),
            is_deleted=is_del,
        )

    def _make_option_action_widget(self, opt):
        opt_id = opt["id"]
        is_del = _is_deleted(opt)
        return self._make_action_widget(
            on_edit=lambda: self._edit_option(opt_id),
            on_action=(lambda: self._restore_option(opt_id)) if is_del
                      else (lambda: self._delete_option(opt_id)),
            is_deleted=is_del,
        )

    # ==========================================
    # DATA POPULATION
    # ==========================================

    def _refresh_all(self):
        prev_cat_id = self._selected_cat_id
        prev_item_id = self._selected_item_id
        cats = self.api.get_categories(include_deleted=self._show_deleted)
        self._categories_data = cats
        self._populate_cats(cats)
        if prev_cat_id:
            self._select_cat_by_id(prev_cat_id, restore_item_id=prev_item_id)
        else:
            self._populate_items([])
            self._populate_options([])

    def _populate_cats(self, cats):
        self.cat_table.setRowCount(0)
        for cat in cats:
            row = self.cat_table.rowCount()
            self.cat_table.insertRow(row)

            name_item = QTableWidgetItem(cat["name"])
            name_item.setData(Qt.UserRole, cat["id"])
            if _is_deleted(cat):
                _apply_deleted_style(name_item)
            self.cat_table.setItem(row, 0, name_item)
            self.cat_table.setCellWidget(row, 1, self._make_cat_action_widget(cat))

    def _populate_items(self, items):
        self.items_table.setRowCount(0)
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            deleted = _is_deleted(item)

            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.UserRole, item["id"])
            if deleted:
                _apply_deleted_style(name_item)
            self.items_table.setItem(row, 0, name_item)

            price_item = QTableWidgetItem(f"{float(item.get('price', 0)):.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if deleted:
                _apply_deleted_style(price_item)
            self.items_table.setItem(row, 1, price_item)

            avail_text = "Oui" if item.get("available", True) else "Non"
            avail_item = QTableWidgetItem(avail_text)
            avail_item.setTextAlignment(Qt.AlignCenter)
            if deleted:
                _apply_deleted_style(avail_item)
            self.items_table.setItem(row, 2, avail_item)

            self.items_table.setCellWidget(row, 3, self._make_item_action_widget(item))

    def _populate_options(self, options):
        self.options_table.setRowCount(0)
        for opt in options:
            row = self.options_table.rowCount()
            self.options_table.insertRow(row)
            deleted = _is_deleted(opt)

            name_item = QTableWidgetItem(opt["name"])
            name_item.setData(Qt.UserRole, opt["id"])
            if deleted:
                _apply_deleted_style(name_item)
            self.options_table.setItem(row, 0, name_item)

            stock_val = opt.get("stock_quantity")
            stock_item = QTableWidgetItem("∞" if stock_val is None else str(stock_val))
            stock_item.setTextAlignment(Qt.AlignCenter)
            if deleted:
                _apply_deleted_style(stock_item)
            self.options_table.setItem(row, 1, stock_item)

            self.options_table.setCellWidget(row, 2, self._make_option_action_widget(opt))

    # ==========================================
    # SELECTION
    # ==========================================

    def _on_cat_cell_clicked(self, row, col):
        if col == self.cat_table.columnCount() - 1:
            return
        it = self.cat_table.item(row, 0)
        if it:
            self._select_cat_by_id(it.data(Qt.UserRole))

    def _select_cat_by_id(self, cat_id, restore_item_id=None):
        self._selected_cat_id = cat_id
        self._selected_opt_id = None
        cat = next((c for c in self._categories_data if c["id"] == cat_id), None)
        if cat:
            items = cat.get("items", [])
            if not self._show_deleted:
                items = [i for i in items if not _is_deleted(i)]
            self._populate_items(items)
            if restore_item_id:
                self._select_item_by_id(restore_item_id)
            else:
                self._selected_item_id = None
                self._populate_options([])
        else:
            self._populate_items([])
            self._selected_item_id = None
            self._populate_options([])

        for r in range(self.cat_table.rowCount()):
            it = self.cat_table.item(r, 0)
            if it and it.data(Qt.UserRole) == cat_id:
                self.cat_table.blockSignals(True)
                self.cat_table.selectRow(r)
                self.cat_table.blockSignals(False)
                break

    def _on_item_cell_clicked(self, row, col):
        if col == self.items_table.columnCount() - 1:
            return
        it = self.items_table.item(row, 0)
        if it:
            self._select_item_by_id(it.data(Qt.UserRole))

    def _select_item_by_id(self, item_id):
        self._selected_item_id = item_id
        self._selected_opt_id = None
        for cat in self._categories_data:
            for item in cat.get("items", []):
                if item["id"] == item_id:
                    opts = item.get("options", [])
                    if not self._show_deleted:
                        opts = [o for o in opts if not _is_deleted(o)]
                    self._populate_options(opts)
                    for r in range(self.items_table.rowCount()):
                        it = self.items_table.item(r, 0)
                        if it and it.data(Qt.UserRole) == item_id:
                            self.items_table.blockSignals(True)
                            self.items_table.selectRow(r)
                            self.items_table.blockSignals(False)
                            break
                    return
        self._populate_options([])

    # ==========================================
    # TOGGLE
    # ==========================================

    def _on_toggle_deleted(self, checked):
        self._show_deleted = checked
        self._refresh_all()

    def _open_bulk_add(self):
        dlg = BulkAddDialog(self, self.api, self._categories_data)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_all()

    def _on_opt_cell_clicked(self, row, col):
        if col == self.options_table.columnCount() - 1:
            return
        it = self.options_table.item(row, 0)
        if it:
            self._selected_opt_id = it.data(Qt.UserRole)
            self.options_table.blockSignals(True)
            self.options_table.selectRow(row)
            self.options_table.blockSignals(False)

    def _top_add(self):
        self._open_bulk_add()

    def _top_edit(self):
        dlg = BulkEditDialog(self, self.api, self._categories_data)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_all()

    def _top_delete(self):
        dlg = BulkDeleteDialog(self, self.api, self._categories_data)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_all()

    # ==========================================
    # CATEGORY CRUD
    # ==========================================

    def _add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec() == QDialog.Accepted:
            result = self.api.create_category(dlg.get_values()["name"])
            if result:
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de creer la categorie.")

    def _edit_category(self, cat_id):
        cat = next((c for c in self._categories_data if c["id"] == cat_id), None)
        if not cat:
            return
        dlg = CategoryDialog(self, name=cat["name"])
        if dlg.exec() == QDialog.Accepted:
            result = self.api.update_category(cat_id, dlg.get_values())
            if result:
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier la categorie.")

    def _delete_category(self, cat_id):
        cat = next((c for c in self._categories_data if c["id"] == cat_id), None)
        name = cat["name"] if cat else str(cat_id)
        reply = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer la categorie '{name}' et tous ses articles ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.api.delete_category(cat_id):
                if self._selected_cat_id == cat_id:
                    self._selected_cat_id = None
                    self._selected_item_id = None
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer la categorie.")

    def _restore_category(self, cat_id):
        if not self.api.restore_category(cat_id):
            QMessageBox.warning(self, "Erreur", "Impossible de restaurer la categorie.")
        else:
            self._refresh_all()

    # ==========================================
    # ITEM CRUD
    # ==========================================

    def _find_item(self, item_id):
        for cat in self._categories_data:
            for it in cat.get("items", []):
                if it["id"] == item_id:
                    return it
        return None

    def _add_item(self):
        if not self._selected_cat_id:
            QMessageBox.information(self, "Info", "Selectionnez une categorie d'abord.")
            return
        dlg = ItemDialog(self, self._categories_data, default_cat_id=self._selected_cat_id)
        if dlg.exec() == QDialog.Accepted:
            if self.api.create_item(dlg.get_values()):
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de creer l'article.")

    def _edit_item(self, item_id):
        item = self._find_item(item_id)
        if not item:
            return
        dlg = ItemDialog(self, self._categories_data, item=item)
        if dlg.exec() == QDialog.Accepted:
            if self.api.update_item(item_id, dlg.get_values()):
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier l'article.")

    def _delete_item(self, item_id):
        item = self._find_item(item_id)
        name = item["name"] if item else str(item_id)
        if QMessageBox.question(
            self, "Confirmer", f"Supprimer l'article '{name}' ?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            if self.api.delete_item(item_id):
                if self._selected_item_id == item_id:
                    self._selected_item_id = None
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'article.")

    def _restore_item(self, item_id):
        if not self.api.restore_item(item_id):
            QMessageBox.warning(self, "Erreur", "Impossible de restaurer l'article.")
        else:
            self._refresh_all()

    # ==========================================
    # OPTION CRUD
    # ==========================================

    def _find_option(self, opt_id):
        for cat in self._categories_data:
            for item in cat.get("items", []):
                for o in item.get("options", []):
                    if o["id"] == opt_id:
                        return o
        return None

    def _add_option(self):
        if not self._selected_item_id:
            QMessageBox.information(self, "Info", "Selectionnez un article d'abord.")
            return
        dlg = OptionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            if self.api.create_item_option(self._selected_item_id, dlg.get_values()):
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de creer l'option.")

    def _edit_option(self, opt_id):
        opt = self._find_option(opt_id)
        if not opt:
            return
        dlg = OptionDialog(self, option=opt)
        if dlg.exec() == QDialog.Accepted:
            if self.api.update_item_option(opt_id, dlg.get_values()):
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier l'option.")

    def _delete_option(self, opt_id):
        opt = self._find_option(opt_id)
        name = opt["name"] if opt else str(opt_id)
        if QMessageBox.question(
            self, "Confirmer", f"Supprimer l'option '{name}' ?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            if self.api.delete_item_option(opt_id):
                self._refresh_all()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'option.")

    def _restore_option(self, opt_id):
        if not self.api.restore_item_option(opt_id):
            QMessageBox.warning(self, "Erreur", "Impossible de restaurer l'option.")
        else:
            self._refresh_all()


# ==========================================
# DIALOGS
# ==========================================

class CategoryDialog(QDialog):
    def __init__(self, parent, name=""):
        super().__init__(parent)
        self.setWindowTitle("Modifier la categorie" if name else "Nouvelle categorie")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Ex: Boissons")
        form.addRow("Nom :", self.name_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btn_ok = QPushButton("Enregistrer")
        btn_ok.clicked.connect(self._validate)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire.")
            return
        self.accept()

    def get_values(self):
        return {"name": self.name_edit.text().strip()}


class ItemDialog(QDialog):
    def __init__(self, parent, categories, item=None, default_cat_id=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier l'article" if item else "Nouvel article")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(item["name"] if item else "")
        self.name_edit.setPlaceholderText("Ex: Espresso")
        form.addRow("Nom :", self.name_edit)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 9999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" EUR")
        if item:
            self.price_spin.setValue(float(item.get("price", 0)))
        form.addRow("Prix :", self.price_spin)

        self.avail_check = QCheckBox("Article disponible a la vente")
        self.avail_check.setChecked(item.get("available", True) if item else True)
        form.addRow("", self.avail_check)

        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(-1, 99999)
        self.stock_spin.setSpecialValueText("Illimite")
        stock_val = item.get("stock_quantity") if item else None
        self.stock_spin.setValue(-1 if stock_val is None else stock_val)
        form.addRow("Stock :", self.stock_spin)

        self.cat_combo = QComboBox()
        active_cats = [c for c in categories if not _is_deleted(c)]
        for cat in active_cats:
            self.cat_combo.addItem(cat["name"], cat["id"])
        target = (item["category_id"] if item else None) or default_cat_id
        if target:
            idx = self.cat_combo.findData(target)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
        form.addRow("Categorie :", self.cat_combo)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btn_ok = QPushButton("Enregistrer")
        btn_ok.clicked.connect(self._validate)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire.")
            return
        if self.cat_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Selectionnez une categorie.")
            return
        self.accept()

    def get_values(self):
        stock = self.stock_spin.value()
        return {
            "name": self.name_edit.text().strip(),
            "price": round(self.price_spin.value(), 2),
            "available": self.avail_check.isChecked(),
            "stock_quantity": None if stock == -1 else stock,
            "category_id": self.cat_combo.currentData(),
        }


class OptionDialog(QDialog):
    def __init__(self, parent, option=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier l'option" if option else "Nouvelle option")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(option["name"] if option else "")
        self.name_edit.setPlaceholderText("Ex: Petit, Grand...")
        form.addRow("Nom :", self.name_edit)

        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(-1, 99999)
        self.stock_spin.setSpecialValueText("∞ Illimité")
        stock_val = option.get("stock_quantity") if option else None
        self.stock_spin.setValue(-1 if stock_val is None else stock_val)
        form.addRow("Stock :", self.stock_spin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btn_ok = QPushButton("Enregistrer")
        btn_ok.clicked.connect(self._validate)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire.")
            return
        self.accept()

    def get_values(self):
        stock = self.stock_spin.value()
        return {
            "name": self.name_edit.text().strip(),
            "stock_quantity": None if stock == -1 else stock,
        }


# ==========================================
# BULK ADD DIALOG
# ==========================================

class BulkAddDialog(QDialog):
    def __init__(self, parent, api_client, categories_data):
        super().__init__(parent)
        self.api = api_client
        self._cats = [c for c in categories_data if not _is_deleted(c)]
        self._items_by_cat = {
            cat["id"]: [i for i in cat.get("items", []) if not _is_deleted(i)]
            for cat in self._cats
        }

        self.setWindowTitle("Ajout en masse")
        self.setMinimumSize(660, 500)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()

        # ---- Categories tab ----
        self._cat_rows = []
        self._cat_rows_layout, cat_scroll = self._make_scroll_tab()
        self.tabs.addTab(cat_scroll, "Categories")
        self._add_cat_row()

        # ---- Items tab ----
        self._item_rows = []
        self._item_rows_layout, item_scroll = self._make_scroll_tab()
        self.tabs.addTab(item_scroll, "Articles")
        self._add_item_row()

        # ---- Options tab ----
        self._opt_rows = []
        self._opt_rows_layout, opt_scroll = self._make_scroll_tab()
        self.tabs.addTab(opt_scroll, "Options")
        self._add_opt_row()

        root.addWidget(self.tabs)

        # Add-row buttons per tab
        self.tabs.currentChanged.connect(self._update_add_btn)
        add_bar = QHBoxLayout()
        self.btn_add_row = QPushButton("+ Ajouter une ligne")
        self.btn_add_row.setObjectName("btn-secondary")
        self.btn_add_row.clicked.connect(self._add_row_for_current_tab)
        add_bar.addWidget(self.btn_add_row)
        add_bar.addStretch()
        root.addLayout(add_bar)

        # Bottom buttons
        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btn_create = QPushButton("Creer tout")
        btn_create.clicked.connect(self._create_all)
        btns.addWidget(btn_create)
        root.addLayout(btns)

    def _make_scroll_tab(self):
        rows_layout = QVBoxLayout()
        rows_layout.setSpacing(4)
        rows_layout.setAlignment(Qt.AlignTop)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(4, 4, 4, 4)
        v.addLayout(rows_layout)
        v.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        return rows_layout, scroll

    def _update_add_btn(self):
        pass  # button always visible, action switches by tab index

    def _add_row_for_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            self._add_cat_row()
        elif idx == 1:
            self._add_item_row()
        else:
            self._add_opt_row()

    def _make_row_widget(self, rows_list, rows_layout):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(8)
        row_dict = {"widget": w, "layout": h}

        def remove():
            rows_list.remove(row_dict)
            rows_layout.removeWidget(w)
            w.deleteLater()

        btn_rm = QPushButton()
        btn_rm.setIcon(qta.icon("fa5s.times", color="#C0392B"))
        btn_rm.setIconSize(QSize(11, 11))
        btn_rm.setFixedSize(26, 26)
        btn_rm.setStyleSheet("background: transparent; border: none;")
        btn_rm.setCursor(Qt.PointingHandCursor)
        btn_rm.clicked.connect(remove)
        row_dict["_rm_btn"] = btn_rm

        rows_list.append(row_dict)
        rows_layout.addWidget(w)
        return row_dict, h, btn_rm

    def _add_cat_row(self):
        row_dict, h, btn_rm = self._make_row_widget(self._cat_rows, self._cat_rows_layout)
        name = QLineEdit()
        name.setPlaceholderText("Nom de la categorie")
        h.addWidget(name, 1)
        h.addWidget(btn_rm)
        row_dict["name"] = name

    def _add_item_row(self):
        row_dict, h, btn_rm = self._make_row_widget(self._item_rows, self._item_rows_layout)

        name = QLineEdit()
        name.setPlaceholderText("Nom")
        h.addWidget(name, 2)

        price = QDoubleSpinBox()
        price.setRange(0, 9999.99)
        price.setDecimals(2)
        price.setSuffix(" EUR")
        h.addWidget(price, 1)

        avail = QCheckBox("Dispo")
        avail.setChecked(True)
        h.addWidget(avail)

        cat_combo = QComboBox()
        for cat in self._cats:
            cat_combo.addItem(cat["name"], cat["id"])
        h.addWidget(cat_combo, 2)

        h.addWidget(btn_rm)
        row_dict.update({"name": name, "price": price, "avail": avail, "cat": cat_combo})

    def _add_opt_row(self):
        row_dict, h, btn_rm = self._make_row_widget(self._opt_rows, self._opt_rows_layout)

        name = QLineEdit()
        name.setPlaceholderText("Nom de l'option")
        h.addWidget(name, 2)

        stock = QSpinBox()
        stock.setRange(-1, 99999)
        stock.setSpecialValueText("∞")
        stock.setValue(-1)
        h.addWidget(stock, 1)

        cat_combo = QComboBox()
        for cat in self._cats:
            cat_combo.addItem(cat["name"], cat["id"])
        h.addWidget(cat_combo, 2)

        item_combo = QComboBox()
        h.addWidget(item_combo, 2)

        def _refresh_items(idx):
            cat_id = cat_combo.currentData()
            item_combo.clear()
            for it in self._items_by_cat.get(cat_id, []):
                item_combo.addItem(it["name"], it["id"])

        cat_combo.currentIndexChanged.connect(_refresh_items)
        if self._cats:
            _refresh_items(0)

        h.addWidget(btn_rm)
        row_dict.update({"name": name, "stock": stock, "cat": cat_combo, "item": item_combo})

    def _create_all(self):
        created, failed = 0, 0

        for row in self._cat_rows:
            name = row["name"].text().strip()
            if name:
                (created := created + 1) if self.api.create_category(name) else (failed := failed + 1)

        for row in self._item_rows:
            name = row["name"].text().strip()
            cat_id = row["cat"].currentData()
            if name and cat_id:
                payload = {
                    "name": name,
                    "price": round(row["price"].value(), 2),
                    "available": row["avail"].isChecked(),
                    "stock_quantity": None,
                    "category_id": cat_id,
                }
                (created := created + 1) if self.api.create_item(payload) else (failed := failed + 1)

        for row in self._opt_rows:
            name = row["name"].text().strip()
            item_id = row["item"].currentData()
            if name and item_id:
                sv = row["stock"].value()
                payload = {"name": name, "stock_quantity": None if sv == -1 else sv}
                result = self.api.create_item_option(item_id, payload)
                (created := created + 1) if result else (failed := failed + 1)

        parts = [f"{created} element(s) cree(s)"]
        if failed:
            parts.append(f"{failed} en erreur")
        QMessageBox.information(self, "Resultat", " — ".join(parts) + ".")
        self.accept()


# ==========================================
# BULK DELETE DIALOG
# ==========================================

class BulkDeleteDialog(QDialog):
    def __init__(self, parent, api_client, categories_data):
        super().__init__(parent)
        self.api = api_client
        self._cats = [c for c in categories_data if not _is_deleted(c)]

        self.setWindowTitle("Suppression")
        self.setMinimumSize(580, 460)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()

        self._cat_checks = []
        cat_scroll, cat_layout = self._make_check_tab()
        for cat in self._cats:
            n = len([i for i in cat.get("items", []) if not _is_deleted(i)])
            label = f"{cat['name']}   ({n} article{'s' if n != 1 else ''})"
            cb = self._make_check(label, cat["id"], self._cat_checks)
            cat_layout.addWidget(cb)
        self.tabs.addTab(cat_scroll, "Categories")

        self._item_checks = []
        item_scroll, item_layout = self._make_check_tab()
        for cat in self._cats:
            for item in cat.get("items", []):
                if not _is_deleted(item):
                    label = f"{item['name']}   {cat['name']}   {float(item.get('price', 0)):.2f} EUR"
                    cb = self._make_check(label, item["id"], self._item_checks)
                    item_layout.addWidget(cb)
        self.tabs.addTab(item_scroll, "Articles")

        self._opt_checks = []
        opt_scroll, opt_layout = self._make_check_tab()
        for cat in self._cats:
            for item in cat.get("items", []):
                if not _is_deleted(item):
                    for opt in item.get("options", []):
                        if not _is_deleted(opt):
                            label = f"{opt['name']}   {item['name']}   stock : {opt.get('stock_quantity', 0)}"
                            cb = self._make_check(label, opt["id"], self._opt_checks)
                            opt_layout.addWidget(cb)
        self.tabs.addTab(opt_scroll, "Options")

        root.addWidget(self.tabs)

        sel_bar = QHBoxLayout()
        sel_bar.setSpacing(8)
        btn_all = QPushButton("Tout cocher")
        btn_all.setObjectName("btn-secondary")
        btn_all.clicked.connect(self._check_all)
        btn_none = QPushButton("Tout decocher")
        btn_none.setObjectName("btn-secondary")
        btn_none.clicked.connect(self._uncheck_all)
        sel_bar.addWidget(btn_all)
        sel_bar.addWidget(btn_none)
        sel_bar.addStretch()
        root.addLayout(sel_bar)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        self.btn_del = QPushButton("Supprimer (0)")
        self.btn_del.setObjectName("btn-danger")
        self.btn_del.setEnabled(False)
        self.btn_del.clicked.connect(self._delete_selected)
        btns.addWidget(self.btn_del)
        root.addLayout(btns)

    def _make_scroll_tab_inner(self):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(8, 8, 8, 8)
        v.addLayout(layout)
        v.addStretch()
        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        return scroll, layout

    def _make_check_tab(self):
        return self._make_scroll_tab_inner()

    def _make_check(self, label, entity_id, checks_list):
        cb = QCheckBox(label)
        cb.setProperty("entity_id", entity_id)
        cb.stateChanged.connect(self._update_btn)
        checks_list.append(cb)
        return cb

    def _current_checks(self):
        idx = self.tabs.currentIndex()
        return [self._cat_checks, self._item_checks, self._opt_checks][idx]

    def _count_checked(self):
        return sum(
            1 for checks in (self._cat_checks, self._item_checks, self._opt_checks)
            for cb in checks if cb.isChecked()
        )

    def _update_btn(self):
        n = self._count_checked()
        self.btn_del.setText(f"Supprimer ({n})")
        self.btn_del.setEnabled(n > 0)

    def _check_all(self):
        for cb in self._current_checks():
            cb.setChecked(True)

    def _uncheck_all(self):
        for cb in self._current_checks():
            cb.setChecked(False)

    def _delete_selected(self):
        cat_ids = [cb.property("entity_id") for cb in self._cat_checks if cb.isChecked()]
        item_ids = [cb.property("entity_id") for cb in self._item_checks if cb.isChecked()]
        opt_ids = [cb.property("entity_id") for cb in self._opt_checks if cb.isChecked()]
        n = len(cat_ids) + len(item_ids) + len(opt_ids)

        if QMessageBox.question(
            self, "Confirmer", f"Supprimer {n} element(s) selectionne(s) ?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return

        done, failed = 0, 0
        for oid in opt_ids:
            (done := done + 1) if self.api.delete_item_option(oid) else (failed := failed + 1)
        for iid in item_ids:
            (done := done + 1) if self.api.delete_item(iid) else (failed := failed + 1)
        for cid in cat_ids:
            (done := done + 1) if self.api.delete_category(cid) else (failed := failed + 1)

        parts = [f"{done} element(s) supprime(s)"]
        if failed:
            parts.append(f"{failed} en erreur")
        QMessageBox.information(self, "Resultat", " — ".join(parts) + ".")
        self.accept()


# ==========================================
# BULK EDIT DIALOG
# ==========================================

class BulkEditDialog(QDialog):
    def __init__(self, parent, api_client, categories_data):
        super().__init__(parent)
        self.api = api_client
        self._cats = [c for c in categories_data if not _is_deleted(c)]
        self._items_by_cat = {
            cat["id"]: [i for i in cat.get("items", []) if not _is_deleted(i)]
            for cat in self._cats
        }

        self.setWindowTitle("Modification")
        self.setMinimumSize(720, 500)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()

        self._cat_rows = []
        cat_scroll, cat_layout = self._make_scroll_tab()
        for cat in self._cats:
            self._add_cat_row(cat_layout, cat)
        self.tabs.addTab(cat_scroll, "Categories")

        self._item_rows = []
        item_scroll, item_layout = self._make_scroll_tab()
        for cat in self._cats:
            for item in self._items_by_cat[cat["id"]]:
                self._add_item_row(item_layout, item)
        self.tabs.addTab(item_scroll, "Articles")

        self._opt_rows = []
        opt_scroll, opt_layout = self._make_scroll_tab()
        for cat in self._cats:
            for item in self._items_by_cat[cat["id"]]:
                for opt in item.get("options", []):
                    if not _is_deleted(opt):
                        self._add_opt_row(opt_layout, opt, item["name"])
        self.tabs.addTab(opt_scroll, "Options")

        root.addWidget(self.tabs)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self._save_all)
        btns.addWidget(btn_save)
        root.addLayout(btns)

    def _make_scroll_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(4, 8, 4, 8)
        v.addLayout(layout)
        v.addStretch()
        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        return scroll, layout

    def _row_container(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(8)
        return w, h

    def _id_label(self, entity_id):
        lbl = QLabel(f"#{entity_id}")
        lbl.setFixedWidth(36)
        lbl.setStyleSheet("color: #6A6055; font-size: 11px;")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _add_cat_row(self, layout, cat):
        w, h = self._row_container()
        h.addWidget(self._id_label(cat["id"]))
        name = QLineEdit(cat["name"])
        h.addWidget(name, 1)
        layout.addWidget(w)
        self._cat_rows.append({
            "id": cat["id"],
            "orig_name": cat["name"],
            "name": name,
        })

    def _add_item_row(self, layout, item):
        w, h = self._row_container()
        h.addWidget(self._id_label(item["id"]))

        name = QLineEdit(item["name"])
        h.addWidget(name, 3)

        price = QDoubleSpinBox()
        price.setRange(0, 9999.99)
        price.setDecimals(2)
        price.setSuffix(" EUR")
        price.setValue(float(item.get("price", 0)))
        h.addWidget(price, 2)

        avail = QCheckBox("Dispo")
        avail.setChecked(item.get("available", True))
        h.addWidget(avail)

        cat_combo = QComboBox()
        for c in self._cats:
            cat_combo.addItem(c["name"], c["id"])
        idx = cat_combo.findData(item["category_id"])
        if idx >= 0:
            cat_combo.setCurrentIndex(idx)
        h.addWidget(cat_combo, 2)

        layout.addWidget(w)
        self._item_rows.append({
            "id": item["id"],
            "orig_name": item["name"],
            "orig_price": float(item.get("price", 0)),
            "orig_available": item.get("available", True),
            "orig_cat_id": item["category_id"],
            "name": name,
            "price": price,
            "avail": avail,
            "cat": cat_combo,
        })

    def _add_opt_row(self, layout, opt, item_name):
        w, h = self._row_container()
        h.addWidget(self._id_label(opt["id"]))

        name = QLineEdit(opt["name"])
        h.addWidget(name, 3)

        stock = QSpinBox()
        stock.setRange(-1, 99999)
        stock.setSpecialValueText("∞")
        sv = opt.get("stock_quantity")
        stock.setValue(-1 if sv is None else sv)
        h.addWidget(stock, 1)

        ctx = QLabel(f"({item_name})")
        ctx.setStyleSheet("color: #6A6055;")
        h.addWidget(ctx, 2)

        layout.addWidget(w)
        self._opt_rows.append({
            "id": opt["id"],
            "orig_name": opt["name"],
            "orig_stock": opt.get("stock_quantity"),
            "name": name,
            "stock": stock,
        })

    def _save_all(self):
        updated, failed = 0, 0

        for row in self._cat_rows:
            name = row["name"].text().strip()
            if name and name != row["orig_name"]:
                (updated := updated + 1) if self.api.update_category(row["id"], {"name": name}) \
                    else (failed := failed + 1)

        for row in self._item_rows:
            name = row["name"].text().strip()
            price = round(row["price"].value(), 2)
            avail = row["avail"].isChecked()
            cat_id = row["cat"].currentData()
            changed = (
                name != row["orig_name"] or
                price != row["orig_price"] or
                avail != row["orig_available"] or
                cat_id != row["orig_cat_id"]
            )
            if changed and name:
                payload = {"name": name, "price": price, "available": avail, "category_id": cat_id}
                (updated := updated + 1) if self.api.update_item(row["id"], payload) \
                    else (failed := failed + 1)

        for row in self._opt_rows:
            name = row["name"].text().strip()
            sv = row["stock"].value()
            stock_val = None if sv == -1 else sv
            changed = name != row["orig_name"] or stock_val != row["orig_stock"]
            if changed and name:
                payload = {"name": name, "stock_quantity": stock_val}
                (updated := updated + 1) if self.api.update_item_option(row["id"], payload) \
                    else (failed := failed + 1)

        if updated == 0 and failed == 0:
            QMessageBox.information(self, "Info", "Aucune modification detectee.")
            return

        parts = [f"{updated} element(s) mis a jour"]
        if failed:
            parts.append(f"{failed} en erreur")
        QMessageBox.information(self, "Resultat", " — ".join(parts) + ".")
        self.accept()
