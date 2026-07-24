import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    # Chargement du style (assure-toi qu'il existe)
    try:
        with open("frontend/styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except:
        pass

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()