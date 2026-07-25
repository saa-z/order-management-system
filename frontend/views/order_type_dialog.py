from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QSpinBox, QStackedWidget, QWidget)


class OrderTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Type de commande")
        self.setModal(True)

        self.order_type = "eat in"
        self.table_number = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # On utilise un QStackedWidget pour passer facilement de la vue 1 à la vue 2
        self.stack = QStackedWidget()

        # --- VUE 1 : Choix du type (Sur place / À emporter) ---
        self.page_choice = QWidget()
        layout_choice = QVBoxLayout(self.page_choice)

        label_choice = QLabel("Choisissez le mode de commande :")
        label_choice.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout_choice.addWidget(label_choice)

        btn_layout = QHBoxLayout()
        btn_eat_in = QPushButton("Sur Place")
        btn_take_away = QPushButton("À Emporter")

        # Style plus visible pour de la caisse
        btn_eat_in.setMinimumHeight(50)
        btn_take_away.setMinimumHeight(50)

        btn_eat_in.clicked.connect(self.on_eat_in_selected)
        btn_take_away.clicked.connect(self.on_take_away_selected)

        btn_layout.addWidget(btn_eat_in)
        btn_layout.addWidget(btn_take_away)
        layout_choice.addLayout(btn_layout)

        # --- VUE 2 : Numéro de table (uniquement pour Sur Place) ---
        self.page_table = QWidget()
        layout_table = QVBoxLayout(self.page_table)

        label_table = QLabel("Saisissez le numéro de table :")
        label_table.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout_table.addWidget(label_table)

        table_input_layout = QHBoxLayout()
        self.spin_table = QSpinBox()
        self.spin_table.setRange(1, 200)
        self.spin_table.setMinimumHeight(35)
        table_input_layout.addWidget(QLabel("Table n° :"))
        table_input_layout.addWidget(self.spin_table)
        layout_table.addLayout(table_input_layout)

        # Boutons de confirmation
        confirm_layout = QHBoxLayout()
        btn_back = QPushButton("Retour")
        btn_valid = QPushButton("Valider")

        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_valid.clicked.connect(self.validate_eat_in)

        confirm_layout.addWidget(btn_back)
        confirm_layout.addWidget(btn_valid)
        layout_table.addLayout(confirm_layout)

        # Ajout des vues au Stack
        self.stack.addWidget(self.page_choice)
        self.stack.addWidget(self.page_table)

        main_layout.addWidget(self.stack)

    def on_eat_in_selected(self):
        """Bascule vers l'étape de saisie de la table."""
        self.order_type = "eat in"
        self.stack.setCurrentIndex(1)

    def on_take_away_selected(self):
        """Valide directement la commande à emporter."""
        self.order_type = "take away"
        self.table_number = None
        self.accept()

    def validate_eat_in(self):
        """Valide la table et ferme la boîte."""
        self.table_number = self.spin_table.value()
        self.accept()