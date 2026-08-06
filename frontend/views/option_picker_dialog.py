from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QSpinBox, QScrollArea, QWidget)
from PySide6.QtCore import Qt


class OptionPickerDialog(QDialog):
    def __init__(self, item_name, options, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Options — {item_name}")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self.spinners = {}
        self.init_ui(item_name, options)

    def init_ui(self, item_name, options):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        title = QLabel(f"Options pour « {item_name} »")
        title.setObjectName("page-title")
        title.setWordWrap(True)
        main_layout.addWidget(title)

        subtitle = QLabel("Sélectionnez les quantités souhaitées")
        subtitle.setObjectName("page-subtitle")
        main_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        for opt in options:
            option_id = opt["id"]
            option_name = opt["name"]
            stock = opt["stock_quantity"]

            row_widget = QWidget()
            row_widget.setObjectName("option-row")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)

            label = QLabel(option_name)
            label.setMinimumWidth(150)
            label.setObjectName("option-name")
            row_layout.addWidget(label, stretch=2)

            stock_label = QLabel(f"stock: {stock}")
            stock_label.setObjectName("stock-warn" if stock <= 3 else "stock-ok")
            row_layout.addWidget(stock_label)

            spinner = QSpinBox()
            spinner.setRange(0, max(stock, 0))
            spinner.setValue(0)
            spinner.setMinimumHeight(34)
            spinner.setMinimumWidth(70)
            spinner.valueChanged.connect(self.update_total)
            row_layout.addWidget(spinner)

            self.spinners[option_id] = {"spinner": spinner, "name": option_name}
            scroll_layout.addWidget(row_widget)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.total_label = QLabel("Total : 0")
        self.total_label.setObjectName("cart-total")
        self.total_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.total_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn-secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)

        btn_validate = QPushButton("Valider")
        btn_validate.setObjectName("btn-primary")
        btn_validate.setCursor(Qt.PointingHandCursor)
        btn_validate.setMinimumHeight(40)
        btn_validate.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_validate)
        main_layout.addLayout(btn_layout)

    def update_total(self):
        total = sum(s["spinner"].value() for s in self.spinners.values())
        self.total_label.setText(f"Total : {total}")

    def get_selected_options(self):
        result = []
        for option_id, data in self.spinners.items():
            qty = data["spinner"].value()
            if qty > 0:
                result.append({
                    "item_option_id": option_id,
                    "name": data["name"],
                    "quantity": qty,
                })
        return result

    def get_total_quantity(self):
        return sum(s["spinner"].value() for s in self.spinners.values())
