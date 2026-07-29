import os
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[styles] introuvable : {qss_path}")
    except Exception as e:
        print(f"[styles] erreur de chargement : {e}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
