# user_management.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QCheckBox, QFormLayout, QGroupBox)

from sqlalchemy import text


class UserManagementPage(QWidget):
    """A page for administrators to manage application users."""

    # --- CORRECTED: The __init__ method now correctly accepts all required arguments from main.py ---
    def __init__(self, db_engine, current_username, log_audit_trail_func):
        super().__init__()
        self.engine = db_engine
        self.current_username = current_username  # To prevent self-deletion/editing
        self.log_audit_trail = log_audit_trail_func

        self.current_editing_user_id = None
        self._setup_ui()
        self.refresh_page()  # Initial load

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Table of Users ---
        table_group = QGroupBox("Existing Users")
        table_layout = QVBoxLayout()

        self.users_table = QTableWidget(
            editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
            selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
            selectionMode=QAbstractItemView.SelectionMode.SingleSelection,
            alternatingRowColors=True
        )
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.users_table)
        table_group.setLayout(table_layout)

        # --- Form for Add/Edit ---
        form_group = QGroupBox("Add / Edit User")
        self.form_layout = QFormLayout()
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Leave empty to keep current password")
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Editor", "Admin"])
        self.qc_access_check = QCheckBox("Has QC Program Access")

        self.form_layout.addRow("Username:", self.username_edit)
        self.form_layout.addRow("New Password:", self.password_edit)
        self.form_layout.addRow("Confirm Password:", self.confirm_password_edit)
        self.form_layout.addRow("Role:", self.role_combo)
        self.form_layout.addRow(self.qc_access_check)
        form_group.setLayout(self.form_layout)

        # --- Action Buttons ---
        self.load_btn = QPushButton("Load Selected User")
        self.save_btn = QPushButton("Save New User")
        self.save_btn.setObjectName("PrimaryButton")
        self.delete_btn = QPushButton("Delete Selected User")
        self.clear_btn = QPushButton("Clear Form / New User")

        top_button_layout = QHBoxLayout()
        top_button_layout.addStretch()
        top_button_layout.addWidget(self.load_btn)
        top_button_layout.addWidget(self.delete_btn)

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.clear_btn)
        bottom_button_layout.addWidget(self.save_btn)

        # --- Assemble Page ---
        main_layout.addWidget(table_group)
        main_layout.addLayout(top_button_layout)
        main_layout.addWidget(form_group)
        main_layout.addLayout(bottom_button_layout)

        # --- Connections ---
        self.load_btn.clicked.connect(self._load_selected_user_to_form)
        self.users_table.doubleClicked.connect(self._load_selected_user_to_form)
        self.save_btn.clicked.connect(self._save_user)
        self.delete_btn.clicked.connect(self._delete_user)
        self.clear_btn.clicked.connect(self._clear_form)

    def refresh_page(self):
        """Public method to be called when the tab is shown."""
        self._load_users()
        self._clear_form()

    def _load_users(self):
        """Fetches all users from the database and populates the table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id, username, role, qc_access FROM users ORDER BY username")).mappings().all()

            self.users_table.setRowCount(0)
            headers = ["ID", "Username", "Role", "QC Access"]
            self.users_table.setColumnCount(len(headers))
            self.users_table.setHorizontalHeaderLabels(headers)

            self.users_table.setRowCount(len(result))
            for row, user in enumerate(result):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
                self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
                self.users_table.setItem(row, 2, QTableWidgetItem(user['role']))
                access_item = QTableWidgetItem("Yes" if user['qc_access'] else "No")
                access_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.users_table.setItem(row, 3, access_item)

                self.users_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user['id'])

            self.users_table.resizeColumnsToContents()
            self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {e}")

    def _clear_form(self):
        """Resets the form to its default state for adding a new user."""
        self.current_editing_user_id = None
        self.username_edit.clear()
        self.username_edit.setReadOnly(False)
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.role_combo.setCurrentText("Editor")
        self.qc_access_check.setChecked(True)
        self.save_btn.setText("Save New User")
        self.users_table.clearSelection()
        self.username_edit.setFocus()

    def _load_selected_user_to_form(self):
        """Populates the form with data from the selected user in the table."""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a user from the table to load.")
            return

        user_id = self.users_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)

        try:
            with self.engine.connect() as conn:
                user = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).mappings().one()

            self._clear_form()
            self.current_editing_user_id = user['id']
            self.username_edit.setText(user['username'])
            self.username_edit.setReadOnly(True)
            self.role_combo.setCurrentText(user['role'])
            self.qc_access_check.setChecked(user['qc_access'])
            self.save_btn.setText("Update User")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not load user data: {e}")

    def _save_user(self):
        """Handles both creating a new user and updating an existing one."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        role = self.role_combo.currentText()
        has_access = self.qc_access_check.isChecked()

        if not username:
            QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Input Error", "Passwords do not match.")
            return

        if self.current_editing_user_id is None and not password:
            QMessageBox.warning(self, "Input Error", "Password is required for new users.")
            return

        try:
            with self.engine.connect() as conn:
                with conn.begin() as transaction:
                    if self.current_editing_user_id:
                        if password:
                            conn.execute(text(
                                "UPDATE users SET password = :pwd, role = :role, qc_access = :access WHERE id = :id"),
                                         {"pwd": password, "role": role, "access": has_access,
                                          "id": self.current_editing_user_id})
                        else:
                            conn.execute(text("UPDATE users SET role = :role, qc_access = :access WHERE id = :id"),
                                         {"role": role, "access": has_access, "id": self.current_editing_user_id})

                        self.log_audit_trail("UPDATE_USER", f"Updated details for user: {username}")
                        QMessageBox.information(self, "Success", f"User '{username}' has been updated.")

                    else:
                        exists = conn.execute(text("SELECT id FROM users WHERE username = :user"),
                                              {"user": username}).scalar_one_or_none()
                        if exists:
                            QMessageBox.critical(self, "Error", f"Username '{username}' already exists.")
                            transaction.rollback()
                            return

                        conn.execute(text(
                            "INSERT INTO users (username, password, role, qc_access) VALUES (:user, :pwd, :role, :access)"),
                                     {"user": username, "pwd": password, "role": role, "access": has_access})
                        self.log_audit_trail("CREATE_USER", f"Created new user: {username}")
                        QMessageBox.information(self, "Success", f"New user '{username}' has been created.")

            self._load_users()
            self._clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the user: {e}")

    def _delete_user(self):
        """Deletes the selected user from the database."""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a user from the table to delete.")
            return

        row = selected_rows[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        username = self.users_table.item(row, 1).text()

        if username == self.current_username:
            QMessageBox.critical(self, "Action Not Allowed", "You cannot delete your own account.")
            return

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to permanently delete the user '{username}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
                        self.log_audit_trail("DELETE_USER", f"Deleted user: {username}")

                QMessageBox.information(self, "Success", f"User '{username}' has been deleted.")
                self._load_users()
                self._clear_form()

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the user: {e}")