from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel


class AccessPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Gestion des Accès"))

        btn_back = QPushButton("Retour")
        btn_back.clicked.connect(lambda: main_window.go_to("MENU"))
        layout.addWidget(btn_back)
        self.setLayout(layout)