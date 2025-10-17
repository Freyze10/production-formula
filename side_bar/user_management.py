# user_management.py - Modern, User-Friendly Design

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QCheckBox, QFormLayout, QFrame,
                             QGridLayout)
from PyQt6.QtGui import QFont
import qtawesome as fa

from sqlalchemy import text


class UserManagementPage(QWidget):
    """A modern page for administrators to manage application users."""

    def __init__(self, db_engine, current_username, log_audit_trail_func):
        super().__init__()
        self.engine = db_engine
        self.current_username = current_username
        self.log_audit_trail = log_audit_trail_func
        self.current_editing_user_id = None
        self._setup_ui()
        self.refresh_page()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)

        # === Header Section ===
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("User Management")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #111827;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Manage user accounts and permissions")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #6B7280;")
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        main_layout.addWidget(header_card)

        # === Users Table Card ===
        table_card = QFrame()
        table_card.setObjectName("ContentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(12)

        table_header = QHBoxLayout()
        table_title = QLabel("Existing Users")
        table_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        table_title.setStyleSheet("color: #111827;")
        table_header.addWidget(table_title)

        self.user_count_label = QLabel("0 users")
        self.user_count_label.setFont(QFont("Segoe UI", 9))
        self.user_count_label.setStyleSheet("color: #6B7280;")
        table_header.addWidget(self.user_count_label)
        table_header.addStretch()

        table_layout.addLayout(table_header)

        self.users_table = QTableWidget(
            editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
            selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
            selectionMode=QAbstractItemView.SelectionMode.SingleSelection,
            alternatingRowColors=True
        )
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.doubleClicked.connect(self._load_selected_user_to_form)
        table_layout.addWidget(self.users_table)

        # Table action buttons
        table_btn_layout = QHBoxLayout()
        table_btn_layout.addStretch()

        self.load_btn = QPushButton(" Load Selected", objectName="InfoButton")
        self.load_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        self.load_btn.clicked.connect(self._load_selected_user_to_form)
        table_btn_layout.addWidget(self.load_btn)

        self.delete_btn = QPushButton(" Delete Selected", objectName="DangerButton")
        self.delete_btn.setIcon(fa.icon('fa5s.trash', color='white'))
        self.delete_btn.clicked.connect(self._delete_user)
        table_btn_layout.addWidget(self.delete_btn)

        table_layout.addLayout(table_btn_layout)

        main_layout.addWidget(table_card, stretch=1)

        # === User Form Card ===
        form_card = QFrame()
        form_card.setObjectName("ContentCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        form_title_layout = QHBoxLayout()
        self.form_title_label = QLabel("Add New User")
        self.form_title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.form_title_label.setStyleSheet("color: #111827;")
        form_title_layout.addWidget(self.form_title_label)
        form_title_layout.addStretch()

        self.clear_btn = QPushButton(" Clear Form", objectName="SecondaryButton")
        self.clear_btn.setIcon(fa.icon('fa5s.eraser', color='white'))
        self.clear_btn.clicked.connect(self._clear_form)
        form_title_layout.addWidget(self.clear_btn)

        form_layout.addLayout(form_title_layout)

        # Grid layout for form fields
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(15)
        grid_layout.setVerticalSpacing(12)

        # Username
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(username_label, 0, 0)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        grid_layout.addWidget(self.username_edit, 0, 1, 1, 3)

        # Password
        password_label = QLabel("New Password:")
        password_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(password_label, 1, 0)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Leave empty to keep current")
        grid_layout.addWidget(self.password_edit, 1, 1)

        # Confirm Password
        confirm_label = QLabel("Confirm:")
        confirm_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(confirm_label, 1, 2)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Re-enter password")
        grid_layout.addWidget(self.confirm_password_edit, 1, 3)

        # Role
        role_label = QLabel("Role:")
        role_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(role_label, 2, 0)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Editor", "Admin", "Viewer"])
        grid_layout.addWidget(self.role_combo, 2, 1)

        # QC Access Checkbox
        self.qc_access_check = QCheckBox("Has QC Program Access")
        self.qc_access_check.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(self.qc_access_check, 2, 2, 1, 2)

        form_layout.addLayout(grid_layout)

        # Save button
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()

        self.save_btn = QPushButton(" Save User", objectName="SuccessButton")
        self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        self.save_btn.setMinimumWidth(150)
        self.save_btn.clicked.connect(self._save_user)
        save_btn_layout.addWidget(self.save_btn)

        form_layout.addLayout(save_btn_layout)

        main_layout.addWidget(form_card)

    def refresh_page(self):
        """Public method to be called when the tab is shown."""
        self._load_users()
        self._clear_form()

    def _load_users(self):
        """Fetches all users from the database and populates the table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id, username, role, qc_access FROM users ORDER BY username")
                ).mappings().all()

            self.users_table.setRowCount(0)
            headers = ["ID", "Username", "Role", "QC Access"]
            self.users_table.setColumnCount(len(headers))
            self.users_table.setHorizontalHeaderLabels(headers)

            self.users_table.setRowCount(len(result))
            for row, user in enumerate(result):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
                self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
                self.users_table.setItem(row, 2, QTableWidgetItem(user['role']))
                access_item = QTableWidgetItem("✓ Yes" if user['qc_access'] else "✗ No")
                access_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.users_table.setItem(row, 3, access_item)

                self.users_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user['id'])

            self.users_table.resizeColumnsToContents()
            self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

            self.user_count_label.setText(f"{len(result)} user{'s' if len(result) != 1 else ''}")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {e}")
            self.user_count_label.setText("Error loading users")

    def _clear_form(self):
        """Resets the form to its default state for adding a new user."""
        self.current_editing_user_id = None
        self.username_edit.clear()
        self.username_edit.setReadOnly(False)
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.role_combo.setCurrentText("Editor")
        self.qc_access_check.setChecked(True)
        self.save_btn.setText(" Save New User")
        self.save_btn.setIcon(fa.icon('fa5s.user-plus', color='white'))
        self.form_title_label.setText("Add New User")
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
                user = conn.execute(
                    text("SELECT * FROM users WHERE id = :id"),
                    {"id": user_id}
                ).mappings().one()

            self._clear_form()
            self.current_editing_user_id = user['id']
            self.username_edit.setText(user['username'])
            self.username_edit.setReadOnly(True)
            self.role_combo.setCurrentText(user['role'])
            self.qc_access_check.setChecked(user['qc_access'])
            self.save_btn.setText(" Update User")
            self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
            self.form_title_label.setText(f"Edit User: {user['username']}")

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
                            conn.execute(
                                text(
                                    "UPDATE users SET password = :pwd, role = :role, qc_access = :access WHERE id = :id"),
                                {"pwd": password, "role": role, "access": has_access,
                                 "id": self.current_editing_user_id}
                            )
                        else:
                            conn.execute(
                                text("UPDATE users SET role = :role, qc_access = :access WHERE id = :id"),
                                {"role": role, "access": has_access, "id": self.current_editing_user_id}
                            )

                        self.log_audit_trail("UPDATE_USER", f"Updated details for user: {username}")
                        QMessageBox.information(self, "Success", f"User '{username}' has been updated successfully!")

                    else:
                        exists = conn.execute(
                            text("SELECT id FROM users WHERE username = :user"),
                            {"user": username}
                        ).scalar_one_or_none()

                        if exists:
                            QMessageBox.critical(self, "Error", f"Username '{username}' already exists.")
                            transaction.rollback()
                            return

                        conn.execute(
                            text(
                                "INSERT INTO users (username, password, role, qc_access) VALUES (:user, :pwd, :role, :access)"),
                            {"user": username, "pwd": password, "role": role, "access": has_access}
                        )
                        self.log_audit_trail("CREATE_USER", f"Created new user: {username}")
                        QMessageBox.information(self, "Success",
                                                f"New user '{username}' has been created successfully!")

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

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the user '{username}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
                        self.log_audit_trail("DELETE_USER", f"Deleted user: {username}")

                QMessageBox.information(self, "Success", f"User '{username}' has been deleted successfully!")
                self._load_users()
                self._clear_form()

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the user: {e}")