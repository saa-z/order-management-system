from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
                               QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
import qtawesome as qta


ROLE_LABELS = {"admin": "Administrateur", "server": "Serveur"}


class AccessPage(QWidget):
    def __init__(self, main_window, api_client):
        super().__init__()
        self.main_window = main_window
        self.api = api_client
        self._show_revoked = False
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        title = QLabel("Gestion des accès")
        title.setObjectName("page-title")
        top_bar.addWidget(title)
        top_bar.addStretch()

        btn_create = QPushButton("+ Créer un compte")
        btn_create.setObjectName("btn-success")
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.clicked.connect(self._create_user)
        top_bar.addWidget(btn_create)

        self.chk_revoked = QCheckBox("Inclure révoqués")
        self.chk_revoked.toggled.connect(self._on_toggle_revoked)
        top_bar.addWidget(self.chk_revoked)

        btn_back = QPushButton("Menu")
        btn_back.setObjectName("btn-nav")
        btn_back.setFixedWidth(110)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.main_window.go_to("MENU"))
        top_bar.addWidget(btn_back)
        layout.addLayout(top_bar)

        subtitle = QLabel(
            "Les administrateurs accèdent à tout l'OMS. Les serveurs accèdent à la "
            "prise de commande et à l'historique uniquement."
        )
        subtitle.setObjectName("text-muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Identifiant", "Mot de passe", "Rôle", "Statut", "Créé le", "Supprimé le", ""]
        )
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 84)
        layout.addWidget(self.table)

    # ==========================================
    # DATA
    # ==========================================

    def _on_toggle_revoked(self, checked):
        self._show_revoked = checked
        self.load_users()

    def load_users(self):
        users = self.api.get_users(include_revoked=self._show_revoked)
        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            active = u.get("active", True)

            name_item = QTableWidgetItem(u.get("username", ""))

            role_item = QTableWidgetItem(ROLE_LABELS.get(u.get("role", ""), u.get("role", "")))
            role_item.setTextAlignment(Qt.AlignCenter)
            if u.get("role") == "admin":
                role_item.setForeground(QColor("#D4A365"))

            status_item = QTableWidgetItem("Actif" if active else "Révoqué")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor("#2D6B45" if active else "#9C2A24"))

            created = u.get("created_at", "")[:10] if u.get("created_at") else "—"
            date_item = QTableWidgetItem(created)
            date_item.setTextAlignment(Qt.AlignCenter)

            deleted = u.get("deleted_at", "")[:10] if u.get("deleted_at") else "—"
            del_item = QTableWidgetItem(deleted)
            del_item.setTextAlignment(Qt.AlignCenter)
            if u.get("deleted_at"):
                del_item.setForeground(QColor("#9C2A24"))

            if not active:
                for it in (name_item, role_item, date_item):
                    f = it.font(); f.setItalic(True); it.setFont(f)
                    it.setForeground(QColor("#A06060"))

            self.table.setItem(row, 0, name_item)
            self.table.setCellWidget(row, 1, self._make_password_cell(u.get("password") or ""))
            self.table.setItem(row, 2, role_item)
            self.table.setItem(row, 3, status_item)
            self.table.setItem(row, 4, date_item)
            self.table.setItem(row, 5, del_item)
            self.table.setCellWidget(row, 6, self._make_actions(u))

    def _make_password_cell(self, password):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(8, 0, 6, 0)
        h.setSpacing(6)

        dots = "●" * max(len(password), 6) if password else "—"
        lbl = QLabel(dots)
        h.addWidget(lbl)
        h.addStretch()

        btn = QPushButton()
        btn.setObjectName("btn-icon")
        btn.setIconSize(QSize(14, 14))
        btn.setFixedSize(28, 24)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip("Afficher / masquer le mot de passe")
        btn.setIcon(qta.icon("fa5s.eye", color="#A09888"))

        shown = {"v": False}

        def toggle():
            shown["v"] = not shown["v"]
            if shown["v"]:
                lbl.setText(password or "—")
                btn.setIcon(qta.icon("fa5s.eye-slash", color="#D4A365"))
            else:
                lbl.setText(dots)
                btn.setIcon(qta.icon("fa5s.eye", color="#A09888"))

        btn.clicked.connect(toggle)
        if password:
            h.addWidget(btn)
        return w

    def _make_actions(self, user):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(6, 0, 6, 0)
        h.setSpacing(6)

        btn_edit = self._icon_btn("fa5s.pen", "Modifier", "#F5F1E6",
                                  lambda: self._edit_user(user))
        h.addWidget(btn_edit)

        if user.get("active", True):
            btn_rev = self._icon_btn("fa5s.user-slash", "Révoquer l'accès", "#C0392B",
                                     lambda: self._revoke_user(user))
            h.addWidget(btn_rev)
        else:
            btn_re = self._icon_btn("fa5s.undo", "Réactiver", "#F5F1E6",
                                    lambda: self._reactivate_user(user))
            h.addWidget(btn_re)
        return w

    @staticmethod
    def _icon_btn(fa_name, tooltip, color, slot):
        btn = QPushButton()
        btn.setObjectName("btn-icon")
        btn.setIcon(qta.icon(fa_name, color=color))
        btn.setIconSize(QSize(15, 15))
        btn.setFixedWidth(30)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        return btn

    # ==========================================
    # ACTIONS
    # ==========================================

    def _create_user(self):
        dlg = UserDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.get_values()
        result = self.api.create_user(v["username"], v["password"], v["role"])
        if isinstance(result, dict) and result.get("error"):
            QMessageBox.warning(self, "Erreur", result["error"])
        elif result:
            self.load_users()
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de créer le compte.")

    def _edit_user(self, user):
        dlg = UserDialog(self, user=user)
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.get_values()
        payload = {"username": v["username"], "password": v["password"], "role": v["role"]}
        result = self.api.update_user(user["id"], payload)
        if isinstance(result, dict) and result.get("error"):
            QMessageBox.warning(self, "Erreur", result["error"])
        elif result:
            self.load_users()
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de modifier le compte.")

    def _revoke_user(self, user):
        if QMessageBox.question(
            self, "Révoquer l'accès",
            f"Révoquer l'accès de « {user['username']} » ?\n"
            "Son historique de commandes est conservé.",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        result = self.api.update_user(user["id"], {"active": False})
        if isinstance(result, dict) and result.get("error"):
            QMessageBox.warning(self, "Erreur", result["error"])
        else:
            self.load_users()

    def _reactivate_user(self, user):
        result = self.api.update_user(user["id"], {"active": True})
        if isinstance(result, dict) and result.get("error"):
            QMessageBox.warning(self, "Erreur", result["error"])
        else:
            self.load_users()


class UserDialog(QDialog):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier le compte" if user else "Nouveau compte")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(user["username"] if user else "")
        self.name_edit.setPlaceholderText("ex : marie")
        form.addRow("Identifiant :", self.name_edit)

        self.pwd_edit = QLineEdit((user.get("password") or "") if user else "")
        self.pwd_edit.setPlaceholderText("mot de passe")
        form.addRow("Mot de passe :", self.pwd_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItem("Serveur", "server")
        self.role_combo.addItem("Administrateur", "admin")
        if user:
            idx = self.role_combo.findData(user.get("role", "server"))
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
        form.addRow("Rôle :", self.role_combo)

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
            QMessageBox.warning(self, "Validation", "L'identifiant est obligatoire.")
            return
        if not self.pwd_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Le mot de passe est obligatoire.")
            return
        self.accept()

    def get_values(self):
        return {
            "username": self.name_edit.text().strip(),
            "password": self.pwd_edit.text().strip(),
            "role": self.role_combo.currentData(),
        }
