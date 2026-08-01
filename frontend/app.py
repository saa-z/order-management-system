import os
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from print_worker import PrintWorker


def main():
    app = QApplication(sys.argv)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base_dir, "styles.qss")
    assets_dir = os.path.join(base_dir, "assets").replace("\\", "/")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read().replace("{ASSETS}", assets_dir)
        app.setStyleSheet(qss)
    except FileNotFoundError:
        print(f"[styles] introuvable : {qss_path}")
    except Exception as e:
        print(f"[styles] erreur de chargement : {e}")

    window = MainWindow()
    window.show()

    # Ouvrière d'impression : le central imprime les jobs créés par les appareils distants.
    print_worker = PrintWorker(window.api_client)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
