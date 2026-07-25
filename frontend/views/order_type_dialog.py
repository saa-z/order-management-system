from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QStackedWidget, QWidget)
from PySide6.QtCore import Qt


class OrderTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Type de commande")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setMinimumHeight(250)

        self.order_type = "eat_in"
        self.seating_location = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        self.stack = QStackedWidget()

        # --- Page 1: Order type ---
        self.page_choice = QWidget()
        layout_choice = QVBoxLayout(self.page_choice)
        layout_choice.setSpacing(16)

        label_choice = QLabel("Mode de commande")
        label_choice.setObjectName("page-title")
        label_choice.setAlignment(Qt.AlignCenter)
        layout_choice.addWidget(label_choice)

        subtitle = QLabel("Choisissez le type de service")
        subtitle.setObjectName("page-subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout_choice.addWidget(subtitle)

        layout_choice.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_eat_in = QPushButton("Sur Place")
        btn_eat_in.setObjectName("menu-card")
        btn_eat_in.setMinimumHeight(80)
        btn_eat_in.setCursor(Qt.PointingHandCursor)
        btn_eat_in.clicked.connect(self.on_eat_in_selected)

        btn_take_away = QPushButton("A Emporter")
        btn_take_away.setObjectName("menu-card")
        btn_take_away.setMinimumHeight(80)
        btn_take_away.setCursor(Qt.PointingHandCursor)
        btn_take_away.clicked.connect(self.on_take_away_selected)

        btn_layout.addWidget(btn_eat_in)
        btn_layout.addWidget(btn_take_away)
        layout_choice.addLayout(btn_layout)
        layout_choice.addStretch()

        # --- Page 2: Seating location ---
        self.page_seating = QWidget()
        layout_seating = QVBoxLayout(self.page_seating)
        layout_seating.setSpacing(16)

        label_seating = QLabel("Emplacement")
        label_seating.setObjectName("page-title")
        label_seating.setAlignment(Qt.AlignCenter)
        layout_seating.addWidget(label_seating)

        subtitle_seating = QLabel("Salle ou terrasse ?")
        subtitle_seating.setObjectName("page-subtitle")
        subtitle_seating.setAlignment(Qt.AlignCenter)
        layout_seating.addWidget(subtitle_seating)

        layout_seating.addSpacing(8)

        seating_layout = QHBoxLayout()
        seating_layout.setSpacing(12)

        btn_indoor = QPushButton("Salle")
        btn_indoor.setObjectName("menu-card")
        btn_indoor.setMinimumHeight(80)
        btn_indoor.setCursor(Qt.PointingHandCursor)
        btn_indoor.clicked.connect(lambda: self.on_seating_selected("indoor"))

        btn_outdoor = QPushButton("Terrasse")
        btn_outdoor.setObjectName("menu-card")
        btn_outdoor.setMinimumHeight(80)
        btn_outdoor.setCursor(Qt.PointingHandCursor)
        btn_outdoor.clicked.connect(lambda: self.on_seating_selected("outdoor"))

        seating_layout.addWidget(btn_indoor)
        seating_layout.addWidget(btn_outdoor)
        layout_seating.addLayout(seating_layout)

        layout_seating.addStretch()

        btn_back_seating = QPushButton("Retour")
        btn_back_seating.setObjectName("btn-secondary")
        btn_back_seating.setCursor(Qt.PointingHandCursor)
        btn_back_seating.setMinimumHeight(40)
        btn_back_seating.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout_seating.addWidget(btn_back_seating)

        self.stack.addWidget(self.page_choice)
        self.stack.addWidget(self.page_seating)

        main_layout.addWidget(self.stack)

    def on_eat_in_selected(self):
        self.order_type = "eat_in"
        self.stack.setCurrentIndex(1)

    def on_take_away_selected(self):
        self.order_type = "take_away"
        self.seating_location = None
        self.accept()

    def on_seating_selected(self, location):
        self.seating_location = location
        self.accept()
