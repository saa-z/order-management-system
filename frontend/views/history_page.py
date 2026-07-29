from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QDialog, QFrame, QMessageBox, QAbstractItemView,
                               QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox,
                               QCompleter, QScrollArea, QCheckBox)
from PySide6.QtCore import Qt, QDate, QStringListModel
from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from views.option_picker_dialog import OptionPickerDialog


class _PassThroughWheelTable(QTableWidget):
    """QTableWidget that forwards wheel events to its parent scroll area
    instead of consuming them. Used inside OrderDetailDialog so that
    scrolling anywhere in the dialog actually scrolls the whole content."""

    def wheelEvent(self, event):
        event.ignore()


STATUS_LABELS = {
    "pending": "En attente",
    "paid": "Payee",
    "cancelled": "Annulee",
}

STATUS_COLORS = {
    "pending": "#B88647",
    "paid": "#5A5550",
    "cancelled": "#9C2A24",
}

ORDER_TYPE_LABELS = {
    "eat_in": "Sur place",
    "take_away": "A emporter",
}


class HistoryPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client

        self.init_ui()
        self.load_history()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        # ── Top bar ──
        top_bar = QHBoxLayout()
        title = QLabel("Historique des commandes")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_refresh = QPushButton("Rafraichir")
        btn_refresh.setObjectName("btn-nav")
        btn_refresh.setFixedWidth(110)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_history)
        top_bar.addWidget(btn_refresh)

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setFixedWidth(110)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)

        layout.addLayout(top_bar)

        # ── Filter bar (2 lignes) ──
        filter_frame = QFrame()
        filter_frame.setObjectName("filter-bar")
        fl = QVBoxLayout(filter_frame)
        fl.setContentsMargins(10, 6, 10, 6)
        fl.setSpacing(5)

        # Ligne 1 : article + dates + Appliquer
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(QLabel("Article :"))
        self._search_article = QLineEdit()
        self._search_article.setPlaceholderText("Rechercher un article…")
        self._search_article.setMinimumWidth(200)
        self._search_article.returnPressed.connect(self._apply_filter)
        self._search_article.textChanged.connect(self._apply_filter)
        self._article_completer = QCompleter([])
        self._article_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._article_completer.setFilterMode(Qt.MatchContains)
        self._article_completer.activated.connect(self._apply_filter)
        self._search_article.setCompleter(self._article_completer)
        row1.addWidget(self._search_article)

        row1.addWidget(QLabel("De :"))
        self._date_from = QDateEdit(QDate(2020, 1, 1))
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("dd/MM/yyyy")
        self._date_from.setMinimumWidth(110)
        row1.addWidget(self._date_from)

        row1.addWidget(QLabel("À :"))
        self._date_to = QDateEdit(QDate.currentDate())
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("dd/MM/yyyy")
        self._date_to.setMinimumWidth(110)
        row1.addWidget(self._date_to)

        row1.addStretch()

        btn_apply = QPushButton("Appliquer")
        btn_apply.setObjectName("btn-secondary")
        btn_apply.setFixedWidth(110)
        btn_apply.setCursor(Qt.PointingHandCursor)
        btn_apply.clicked.connect(self._apply_filter)
        row1.addWidget(btn_apply)

        fl.addLayout(row1)

        # Ligne 2 : prix + tri + Réinitialiser
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(QLabel("Prix min :"))
        self._price_min = QDoubleSpinBox()
        self._price_min.setRange(0, 9999)
        self._price_min.setDecimals(2)
        self._price_min.setSuffix(" €")
        self._price_min.setMinimumWidth(100)
        row2.addWidget(self._price_min)

        row2.addWidget(QLabel("max :"))
        self._price_max = QDoubleSpinBox()
        self._price_max.setRange(0, 9999)
        self._price_max.setValue(9999)
        self._price_max.setDecimals(2)
        self._price_max.setSuffix(" €")
        self._price_max.setMinimumWidth(100)
        row2.addWidget(self._price_max)

        row2.addWidget(QLabel("Tri :"))
        self._sort_col = QComboBox()
        self._sort_col.addItems(["Date", "Prix", "Statut"])
        self._sort_col.setMinimumWidth(90)
        row2.addWidget(self._sort_col)

        self._sort_order = QComboBox()
        self._sort_order.addItems(["↓ Desc", "↑ Asc"])
        self._sort_order.setMinimumWidth(90)
        row2.addWidget(self._sort_order)

        row2.addStretch()

        btn_reset_f = QPushButton("Réinitialiser")
        btn_reset_f.setObjectName("btn-secondary")
        btn_reset_f.setFixedWidth(110)
        btn_reset_f.setCursor(Qt.PointingHandCursor)
        btn_reset_f.clicked.connect(self._reset_filter)
        row2.addWidget(btn_reset_f)

        fl.addLayout(row2)
        layout.addWidget(filter_frame)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Type", "Couverts", "Total", "Serveur", "Statut"])
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

    def load_history(self):
        try:
            orders = self.api.get_orders()
            self._all_orders = orders
            names = sorted({
                item.get('item_name_snapshot') or ''
                for o in orders
                for item in o.get('items', [])
                if item.get('item_name_snapshot')
            })
            self._article_completer.setModel(QStringListModel(names))
            self._apply_filter()
        except Exception as e:
            import traceback
            print(f"Could not load history: {e}")
            traceback.print_exc()

    def _apply_filter(self):
        orders = list(getattr(self, '_all_orders', []))

        # Article search
        q = self._search_article.text().strip().lower()
        if q:
            orders = [
                o for o in orders
                if any(q in (item.get('item_name_snapshot') or '').lower()
                       for item in o.get('items', []))
            ]

        # Date range
        from_date = self._date_from.date()
        to_date = self._date_to.date()
        filtered = []
        for o in orders:
            date_raw = o.get('created_at', '')
            if date_raw and 'T' in date_raw:
                try:
                    parts = date_raw[:10].split('-')
                    order_date = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    if order_date < from_date or order_date > to_date:
                        continue
                except Exception:
                    pass
            filtered.append(o)
        orders = filtered

        # Price range
        p_min = self._price_min.value()
        p_max = self._price_max.value()
        if p_min > 0 or p_max < 9999:
            def _price(o):
                raw = o.get('total_price')
                return float(raw) if raw is not None else 0.0
            orders = [o for o in orders if p_min <= _price(o) <= p_max]

        # Sort
        sort_col = self._sort_col.currentText()
        asc = self._sort_order.currentText().startswith("↑")
        if sort_col == "Prix":
            def _key(o):
                raw = o.get('total_price')
                return float(raw) if raw is not None else 0.0
        elif sort_col == "Statut":
            _status_order = {"pending": 0, "paid": 1, "cancelled": 2}
            def _key(o):
                return _status_order.get(o.get('status', ''), 99)
        else:
            def _key(o):
                return o.get('created_at', '')
        orders.sort(key=_key, reverse=not asc)

        self._populate_table(orders)

    def _reset_filter(self):
        self._search_article.clear()
        self._date_from.setDate(QDate(2020, 1, 1))
        self._date_to.setDate(QDate.currentDate())
        self._price_min.setValue(0)
        self._price_max.setValue(9999)
        self._sort_col.setCurrentIndex(0)
        self._sort_order.setCurrentIndex(0)
        self._apply_filter()

    def _populate_table(self, orders):
        self.table.setRowCount(0)
        for order in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(order.get("id", "")))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            date_raw = str(order.get("created_at", ""))
            date_display = date_raw[:16].replace("T", " ") if "T" in date_raw else date_raw
            date_item = QTableWidgetItem(date_display)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, date_item)

            type_text = ORDER_TYPE_LABELS.get(order.get("order_type", ""), order.get("order_type", ""))
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

            covers = order.get("covers")
            covers_item = QTableWidgetItem(str(covers) if covers else "—")
            covers_item.setTextAlignment(Qt.AlignCenter)
            covers_item.setFlags(covers_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, covers_item)

            raw_price = order.get('total_price')
            price_item = QTableWidgetItem(f"{float(raw_price):.2f} €" if raw_price is not None else "0.00 €")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, price_item)

            user_data = order.get("created_by")
            user_text = user_data.get("username", "—") if user_data else "—"
            user_item = QTableWidgetItem(user_text)
            user_item.setTextAlignment(Qt.AlignCenter)
            user_item.setFlags(user_item.flags() & ~Qt.ItemIsEditable)
            if user_data:
                user_item.setForeground(QColor("#D4A365"))
            self.table.setItem(row, 5, user_item)

            status_key = order.get("status", "")
            status_text = STATUS_LABELS.get(status_key, status_key)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            color = STATUS_COLORS.get(status_key, "#F5F1E6")
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 6, status_item)

            id_item.setData(Qt.UserRole, order)

    def _on_double_click(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        order = id_item.data(Qt.UserRole)
        if order:
            dlg = OrderDetailDialog(order, self.api, self)
            dlg.exec()
            self.load_history()


class OrderDetailDialog(QDialog):
    def __init__(self, order, api, parent=None):
        super().__init__(parent)
        self._api = api
        self._order = order
        self._order_id = order.get("id")
        self.setWindowTitle(f"Commande #{order.get('id', '')}")
        self.setMinimumWidth(560)
        self.setMinimumHeight(480)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(20, 16, 20, 16)

        # ── Header ──
        status_key = order.get("status", "")
        status_text = STATUS_LABELS.get(status_key, status_key)
        color = STATUS_COLORS.get(status_key, "#F5F1E6")

        h = QHBoxLayout()
        lbl_id = QLabel(f"Commande #{order.get('id', '')}")
        lbl_id.setObjectName("section-header")
        h.addWidget(lbl_id)
        h.addStretch()
        lbl_status = QLabel(status_text)
        lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        h.addWidget(lbl_status)
        root.addLayout(h)

        # ── Meta ──
        date_raw = str(order.get("created_at", ""))
        date_display = date_raw[:16].replace("T", " ") if "T" in date_raw else date_raw
        type_text = ORDER_TYPE_LABELS.get(order.get("order_type", ""), order.get("order_type", ""))

        meta_lines = [f"Date : {date_display}", f"Type : {type_text}"]
        if order.get("table_number"):
            meta_lines.append(f"Table : {order['table_number']}")
        if order.get("covers"):
            meta_lines.append(f"Couverts : {order['covers']}")
        if order.get("customer_name"):
            meta_lines.append(f"Client : {order['customer_name']}")
        if order.get("pickup_time"):
            meta_lines.append(f"Retrait : {order['pickup_time']}")
        user_data = order.get("created_by")
        if user_data:
            meta_lines.append(f"Serveur : {user_data.get('username', '—')}")

        meta = QLabel("   |   ".join(meta_lines))
        meta.setObjectName("text-muted")
        meta.setWordWrap(True)
        root.addWidget(meta)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        root.addWidget(sep)

        # ── Items grouped by batch ──
        items_data = order.get("items", [])
        self._batches: dict[int, list] = {}
        for item in items_data:
            b = item.get("batch", 1) or 1
            self._batches.setdefault(b, []).append(item)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(10)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        for batch_num in sorted(self._batches.keys()):
            batch_items = self._batches[batch_num]

            batch_header = QHBoxLayout()
            lbl_batch = QLabel(f"Bon {batch_num}")
            lbl_batch.setObjectName("batch-header")
            batch_header.addWidget(lbl_batch)
            inner_layout.addLayout(batch_header)

            table = _PassThroughWheelTable(0, 4)
            table.setHorizontalHeaderLabels(["Article", "Options", "Qté", "P.U."])
            table.verticalHeader().hide()
            table.setShowGrid(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

            for order_item in batch_items:
                r = table.rowCount()
                table.insertRow(r)
                name = order_item.get("item_name_snapshot") or ""
                table.setItem(r, 0, QTableWidgetItem(name))
                opts = order_item.get("selected_options", [])
                opts_text = ", ".join(
                    f"{o.get('option_name_snapshot', '')} x{o.get('quantity', 1)}"
                    for o in opts
                ) if opts else "—"
                opt_item = QTableWidgetItem(opts_text)
                opt_item.setForeground(QColor("#A09888"))
                table.setItem(r, 1, opt_item)
                qty_item = QTableWidgetItem(str(order_item.get("quantity", 1)))
                qty_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, 2, qty_item)
                raw_up = order_item.get("unit_price")
                price_item = QTableWidgetItem(f"{float(raw_up):.2f} €" if raw_up is not None else "0.00 €")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(r, 3, price_item)
                if order_item.get("comment"):
                    cr = table.rowCount()
                    table.insertRow(cr)
                    cmt = QTableWidgetItem(f"  ↳ {order_item['comment']}")
                    cmt.setForeground(QColor("#7A7060"))
                    cmt.setFlags(cmt.flags() & ~Qt.ItemIsSelectable)
                    table.setItem(cr, 0, cmt)
                    table.setSpan(cr, 0, 1, 4)

            # Force each row to compute its real content height (padding, etc.)
            table.resizeRowsToContents()
            header_h = table.horizontalHeader().sizeHint().height()
            rows_h = sum(table.rowHeight(r) for r in range(table.rowCount()))
            table.setFixedHeight(header_h + rows_h + 8)
            inner_layout.addWidget(table)

            if batch_num < max(self._batches.keys()):
                div = QFrame()
                div.setObjectName("separator")
                div.setFrameShape(QFrame.HLine)
                inner_layout.addWidget(div)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # ── Total + actions ──
        raw_total = order.get("total_price")
        total_lbl = QLabel(f"Total : {float(raw_total):.2f} €" if raw_total is not None else "Total : 0.00 €")
        total_lbl.setObjectName("cart-total")
        total_lbl.setAlignment(Qt.AlignRight)
        root.addWidget(total_lbl)

        h2 = QHBoxLayout()
        if status_key == "pending":
            btn_add = QPushButton("+ Ajouter des articles")
            btn_add.setObjectName("btn-success")
            btn_add.clicked.connect(self._open_add_items)
            h2.addWidget(btn_add)
            btn_cancel_order = QPushButton("Annuler la commande")
            btn_cancel_order.setObjectName("btn-cancel-order")
            btn_cancel_order.clicked.connect(self._cancel_order)
            h2.addWidget(btn_cancel_order)
        h2.addStretch()
        if len(self._batches) > 0:
            btn_print_batch = QPushButton("Imprimer bon(s)")
            btn_print_batch.setObjectName("btn-secondary")
            btn_print_batch.clicked.connect(self._open_batch_print_dialog)
            h2.addWidget(btn_print_batch)
        btn_print_all = QPushButton("Facturer")
        btn_print_all.setObjectName("btn-secondary")
        btn_print_all.clicked.connect(self._print_all)
        h2.addWidget(btn_print_all)
        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("btn-secondary")
        btn_close.clicked.connect(self.accept)
        h2.addWidget(btn_close)
        root.addLayout(h2)

    def _open_batch_print_dialog(self):
        dlg = BatchSelectDialog(sorted(self._batches.keys()), self)
        if dlg.exec() != QDialog.Accepted:
            return
        selected = dlg.selected_batches()
        if not selected:
            QMessageBox.warning(self, "Aucune sélection", "Sélectionnez au moins un envoi.")
            return
        html_parts = [self._build_batch_html(bn, self._batches[bn]) for bn in selected]
        combined = "<br><hr style='margin:12px 0'><br>".join(html_parts)
        self._do_print(f"<html><body>{combined}</body></html>")

    def _build_batch_html(self, batch_num, batch_items):
        order = self._order
        date_raw = str(order.get("created_at", ""))
        date_display = date_raw[:16].replace("T", " ") if "T" in date_raw else date_raw
        type_text = ORDER_TYPE_LABELS.get(order.get("order_type", ""), "")
        lines = [
            f"<div style='font-family:monospace; font-size:12px;'>",
            f"<h2 style='margin:0'>San Giorgio — Bon {batch_num}</h2>",
            f"<p>Commande #{order.get('id')} | {date_display} | {type_text}</p>",
        ]
        if order.get("table_number"):
            lines.append(f"<p>Table : {order['table_number']}</p>")
        if order.get("covers"):
            lines.append(f"<p>Couverts : {order['covers']}</p>")
        user_data = order.get("created_by")
        if user_data:
            lines.append(f"<p>Serveur : {user_data.get('username', '')}</p>")
        lines.append("<hr><table width='100%' cellspacing='0'>")
        lines.append("<tr><th align='left'>Article</th><th align='left'>Options</th><th align='center'>Qté</th></tr>")
        for item in batch_items:
            name = item.get("item_name_snapshot", "")
            opts = item.get("selected_options", [])
            opts_text = ", ".join(f"{o.get('option_name_snapshot', '')} x{o.get('quantity', 1)}" for o in opts) if opts else ""
            qty = item.get("quantity", 1)
            lines.append(f"<tr><td>{name}</td><td style='color:#666'>{opts_text}</td><td align='center'>{qty}</td></tr>")
            if item.get("comment"):
                lines.append(f"<tr><td colspan='3' style='color:#888; padding-left:12px'>↳ {item['comment']}</td></tr>")
        lines.append("</table></div>")
        return "".join(lines)

    def _build_receipt_html(self):
        order = self._order
        date_raw = str(order.get("created_at", ""))
        date_display = date_raw[:16].replace("T", " ") if "T" in date_raw else date_raw
        type_text = ORDER_TYPE_LABELS.get(order.get("order_type", ""), "")
        lines = [
            "<html><body style='font-family:monospace; font-size:12px;'>",
            f"<h2 style='margin:0'>San Giorgio</h2>",
            f"<p>Commande #{order.get('id')} | {date_display}</p>",
            f"<p>Type : {type_text}</p>",
        ]
        if order.get("table_number"):
            lines.append(f"<p>Table : {order['table_number']}</p>")
        if order.get("covers"):
            lines.append(f"<p>Couverts : {order['covers']}</p>")
        if order.get("customer_name"):
            lines.append(f"<p>Client : {order['customer_name']}</p>")
        lines.append("<hr><table width='100%' cellspacing='0'>")
        lines.append("<tr><th align='left'>Article</th><th align='left'>Options</th><th align='center'>Qté</th><th align='right'>P.U.</th><th align='right'>Total</th></tr>")
        items_data = order.get("items", [])
        for item in items_data:
            name = item.get("item_name_snapshot", "")
            opts = item.get("selected_options", [])
            opts_text = ", ".join(f"{o.get('option_name_snapshot', '')} x{o.get('quantity', 1)}" for o in opts) if opts else ""
            qty = item.get("quantity", 1)
            raw_up = item.get("unit_price")
            up = float(raw_up) if raw_up is not None else 0.0
            lines.append(f"<tr><td>{name}</td><td style='color:#666'>{opts_text}</td><td align='center'>{qty}</td><td align='right'>{up:.2f} €</td><td align='right'>{up * qty:.2f} €</td></tr>")
            if item.get("comment"):
                lines.append(f"<tr><td colspan='5' style='color:#888; padding-left:12px'>↳ {item['comment']}</td></tr>")
        raw_total = order.get("total_price")
        total = float(raw_total) if raw_total is not None else 0.0
        lines.append(f"</table><hr><p align='right'><b>TOTAL : {total:.2f} €</b></p>")
        lines.append("</body></html>")
        return "".join(lines)

    def _do_print(self, html: str):
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.Accepted:
            return
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

    def _print_batch(self, batch_num, batch_items):
        self._do_print(self._build_batch_html(batch_num, batch_items))

    def _print_all(self):
        self._do_print(self._build_receipt_html())

    def _cancel_order(self):
        reply = QMessageBox.question(
            self, "Annuler la commande",
            f"Annuler la commande #{self._order_id} ? Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        result = self._api.update_order_status(self._order_id, "cancelled")
        if result:
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'annuler la commande.")

    def _open_add_items(self):
        cats = self._api.get_categories()
        if not cats:
            QMessageBox.warning(self, "Erreur", "Impossible de charger le menu.")
            return
        dlg = AddItemsDialog(self._order_id, self._api, cats, self)
        if dlg.exec() == QDialog.Accepted:
            self.accept()


# ==========================================
# BATCH SELECT DIALOG
# ==========================================

class BatchSelectDialog(QDialog):
    def __init__(self, batch_numbers: list[int], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sélectionner les envois à imprimer")
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        lbl = QLabel("Cochez les envois à imprimer :")
        layout.addWidget(lbl)

        self._checkboxes: list[tuple[int, QCheckBox]] = []
        for bn in batch_numbers:
            cb = QCheckBox(f"Bon {bn}")
            cb.setChecked(True)
            layout.addWidget(cb)
            self._checkboxes.append((bn, cb))

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Imprimer")
        btn_ok.setObjectName("btn-primary")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def selected_batches(self) -> list[int]:
        return [bn for bn, cb in self._checkboxes if cb.isChecked()]


# ==========================================
# ADD ITEMS DIALOG (mini-POS)
# ==========================================

class AddItemsDialog(QDialog):
    def __init__(self, order_id, api, categories, parent=None):
        super().__init__(parent)
        self._order_id = order_id
        self._api = api
        self._categories = {c["name"]: c["items"] for c in categories}
        self._cart = []  # list of item_data dicts

        self.setWindowTitle(f"Ajouter des articles — Commande #{order_id}")
        self.setMinimumSize(740, 500)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 14, 16, 14)

        body = QHBoxLayout()
        body.setSpacing(12)

        # ── Catégories ──
        self._cat_table = QTableWidget(0, 1)
        self._cat_table.setObjectName("cat-table")
        self._cat_table.horizontalHeader().hide()
        self._cat_table.verticalHeader().hide()
        self._cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._cat_table.setShowGrid(False)
        self._cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._cat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._cat_table.setFixedWidth(150)
        self._cat_table.itemClicked.connect(self._on_cat_clicked)
        for name in self._categories:
            r = self._cat_table.rowCount()
            self._cat_table.insertRow(r)
            it = QTableWidgetItem(name)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self._cat_table.setItem(r, 0, it)
        body.addWidget(self._cat_table)

        # ── Articles ──
        self._item_table = QTableWidget(0, 2)
        self._item_table.setObjectName("items-table")
        self._item_table.setHorizontalHeaderLabels(["Article", "Prix"])
        self._item_table.verticalHeader().hide()
        self._item_table.setShowGrid(False)
        self._item_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._item_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._item_table.cellClicked.connect(self._on_item_clicked)
        body.addWidget(self._item_table, 2)

        # ── Panier ──
        right = QVBoxLayout()
        right.setSpacing(6)
        cart_lbl = QLabel("À ajouter")
        cart_lbl.setObjectName("section-header")
        right.addWidget(cart_lbl)

        self._cart_table = QTableWidget(0, 3)
        self._cart_table.setObjectName("cart-table")
        self._cart_table.setHorizontalHeaderLabels(["Article", "Qté", "Prix"])
        self._cart_table.verticalHeader().hide()
        self._cart_table.setShowGrid(False)
        self._cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        right.addWidget(self._cart_table)

        self._total_lbl = QLabel("Total à ajouter : 0.00 €")
        self._total_lbl.setObjectName("cart-total")
        self._total_lbl.setAlignment(Qt.AlignRight)
        right.addWidget(self._total_lbl)

        btn_clear = QPushButton("Vider le panier")
        btn_clear.setObjectName("btn-secondary")
        btn_clear.clicked.connect(self._clear_cart)
        right.addWidget(btn_clear)

        body.addLayout(right, 2)
        root.addLayout(body)

        # ── Boutons bas ──
        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        self._btn_confirm = QPushButton("Envoyer en cuisine")
        self._btn_confirm.setObjectName("btn-kitchen")
        self._btn_confirm.clicked.connect(self._confirm)
        btns.addWidget(self._btn_confirm)
        root.addLayout(btns)

    def _on_cat_clicked(self, item):
        self._item_table.setRowCount(0)
        for it in self._categories.get(item.text(), []):
            if it.get("deleted_at"):
                continue
            r = self._item_table.rowCount()
            self._item_table.insertRow(r)
            name_item = QTableWidgetItem(it["name"])
            name_item.setData(Qt.UserRole, it)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self._item_table.setItem(r, 0, name_item)
            price_item = QTableWidgetItem(f"{float(it['price']):.2f} €")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self._item_table.setItem(r, 1, price_item)

    def _on_item_clicked(self, row, col):
        it = self._item_table.item(row, 0)
        if not it:
            return
        item_data = it.data(Qt.UserRole).copy()
        if not item_data.get("is_in_stock", True):
            QMessageBox.warning(self, "Rupture", f"« {item_data['name']} » n'est plus disponible.")
            return

        selected_options = None
        qty = 1
        options = item_data.get("options", [])
        if options:
            available = [o for o in options if o.get("stock_quantity") is None or o["stock_quantity"] > 0]
            if not available:
                QMessageBox.warning(self, "Rupture", f"Toutes les options de « {item_data['name']} » sont en rupture.")
                return
            dlg = OptionPickerDialog(item_data["name"], available, self)
            if dlg.exec() != QDialog.Accepted:
                return
            selected_options = dlg.get_selected_options()
            if not selected_options:
                QMessageBox.warning(self, "Aucune sélection", "Sélectionnez au moins une option.")
                return
            qty = dlg.get_total_quantity()

        item_data["selected_options"] = selected_options
        item_data["comment"] = None
        self._cart.append({"item_data": item_data, "qty": qty})
        self._refresh_cart()

    def _refresh_cart(self):
        self._cart_table.setRowCount(0)
        total = 0.0
        for entry in self._cart:
            d = entry["item_data"]
            r = self._cart_table.rowCount()
            self._cart_table.insertRow(r)
            display = d["name"]
            if d.get("selected_options"):
                opts = ", ".join(f"{o['name']} x{o['quantity']}" for o in d["selected_options"])
                display += f" ({opts})"
            self._cart_table.setItem(r, 0, QTableWidgetItem(display))
            qty_item = QTableWidgetItem(str(entry["qty"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self._cart_table.setItem(r, 1, qty_item)
            price = float(d["price"]) * entry["qty"]
            total += price
            p_item = QTableWidgetItem(f"{price:.2f} €")
            p_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._cart_table.setItem(r, 2, p_item)
        self._total_lbl.setText(f"Total à ajouter : {total:.2f} €")

    def _clear_cart(self):
        self._cart.clear()
        self._refresh_cart()

    def _confirm(self):
        if not self._cart:
            QMessageBox.warning(self, "Panier vide", "Ajoutez au moins un article.")
            return
        items_payload = []
        for entry in self._cart:
            d = entry["item_data"]
            selected = None
            if d.get("selected_options"):
                selected = [
                    {"item_option_id": o["item_option_id"], "quantity": o["quantity"]}
                    for o in d["selected_options"]
                ]
            items_payload.append({
                "item_id": d["id"],
                "quantity": entry["qty"],
                "comment": d.get("comment"),
                "selected_options": selected,
            })
        result = self._api.add_order_items(self._order_id, items_payload)
        if result:
            QMessageBox.information(self, "Succès", "Articles ajoutés à la commande.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'ajouter les articles (stock insuffisant ou commande fermée).")
