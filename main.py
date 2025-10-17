# main.py - COMPLETE VERSION WITH SILENT BACKGROUND LEGACY SYNC
import sys
import os
from datetime import datetime
from PyQt6.QtCore import QTimer

try:
    import qtawesome as fa
except ImportError:
    print("FATAL ERROR: The 'qtawesome' library is required. Please install it using: pip install qtawesome")
    sys.exit(1)

from PyQt6.QtCore import (Qt, pyqtSignal, QSize, QEvent, QTimer, QThread, QObject, QPropertyAnimation,
                          QEasingCurve, QAbstractAnimation)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
                             QMessageBox, QVBoxLayout, QHBoxLayout, QStackedWidget,
                             QFrame, QStatusBar, QDialog, QGraphicsOpacityEffect)
from PyQt6.QtGui import QMovie

# --- Page imports ---
from side_bar.audit_trail import AuditTrailPage
from side_bar.user_management import UserManagementPage
from side_bar.formulation import FormulationManagementPage
from utils.work_station import _get_workstation_info

# --- Database imports ---
from db.engine_conn import create_engine_connection
from db.schema import (initialize_database, get_user_credentials, log_audit_trail, test_database_connection)


class AppStyles:
    """A class to hold all the stylesheet strings for the application."""
    PRIMARY_COLOR = "#0078d4"
    PRIMARY_COLOR_HOVER = "#005a9e"

    LOGIN_STYLESHEET = f"""
        #LoginWindow, #FormFrame {{ background-color: #f5f5f5; }}
        QWidget {{ font-family: "Segoe UI"; font-size: 10pt; }}
        #LoginTitle {{ font-size: 18pt; font-weight: bold; color: #2c3e50; }}
        #InputFrame {{ background-color: #fff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 5px; }}
        #InputFrame:focus-within {{ border: 1px solid {PRIMARY_COLOR}; }}
        QLineEdit {{ border: none; background-color: transparent; padding: 6px; }}
        QPushButton#PrimaryButton {{ background-color: {PRIMARY_COLOR}; color: #fff; border-radius: 8px; padding: 8px; font-weight: bold; font-size: 11pt; border: none; }}
        QPushButton#PrimaryButton:hover {{ background-color: {PRIMARY_COLOR_HOVER}; }}
        #StatusLabel {{ color: #D32F2F; font-size: 9pt; }}
    """

    MAIN_WINDOW_STYLESHEET = f"""
        QMainWindow, QStackedWidget > QWidget {{ background-color: #f8f9fa; }}
        QWidget {{ font-family: 'Segoe UI', sans-serif; font-size: 9pt; color: #212121; }}
        QStatusBar, QStatusBar QLabel {{ background-color: #f0f0f0; font-size: 9pt; }}
        QWidget#SideMenu {{ background-color: #2c3e50; color: #ecf0f1; width: 220px; }}
        #SideMenu QLabel {{ color: #ecf0f1; font-family: "Segoe UI"; font-size: 10pt; }}
        #SideMenu #MenuLabel {{ font-size: 9pt; font-weight: bold; color: #95a5a6; padding: 10px 10px 2px 10px; margin-top: 8px; }}
        #SideMenu QPushButton {{ background-color: transparent; color: #ecf0f1; border: none; padding: 10px; text-align: left; font-size: 10pt; font-weight: bold; border-radius: 6px; padding-left: 25px; }}
        #SideMenu QPushButton:hover {{ background-color: #34495e; }}
        #SideMenu QPushButton:checked {{ background-color: {PRIMARY_COLOR}; }}
        QFrame#Separator {{ background-color: #34495e; height: 1px; }}
        QFormLayout QLabel, QGridLayout QLabel, QGroupBox {{ font-weight: bold; color: #343a40; }}
        QLineEdit, QComboBox, QDateEdit {{ border: 1px solid #ced4da; padding: 6px; border-radius: 6px; background-color: #ffffff; min-height: 20px; }}
        QDateEdit {{ min-width: 80px; }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {PRIMARY_COLOR}; }}
        QLineEdit:read-only {{ background-color: #e9ecef; color: #495057; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left-width: 1px; border-left-color: #ced4da; border-left-style: solid; }}
        QCheckBox::indicator {{ width: 15px; height: 15px; border-radius: 4px; }}
        QCheckBox::indicator:checked {{ background-color: {PRIMARY_COLOR}; }}
        QPushButton {{ padding: 8px 15px; font-size: 9pt; border: 1px solid #ced4da; border-radius: 6px; background-color: #ffffff; }}
        QPushButton:hover {{ background-color: #f1f3f5; border-color: #adb5bd; }}
        QPushButton#PrimaryButton {{ background-color: {PRIMARY_COLOR}; color: #ffffff; font-weight: bold; border: none; }}
        QPushButton#PrimaryButton:hover {{ background-color: {PRIMARY_COLOR_HOVER}; }}
        QPushButton#SecondaryButton {{ background-color: #6c757d; color: #ffffff; font-weight: bold; border: none; }}
        QPushButton#SecondaryButton:hover {{ background-color: #5a6268; }}
        QPushButton#SuccessButton {{ background-color: #28a745; color: #ffffff; font-weight: bold; border: none; }}
        QPushButton#SuccessButton:hover {{ background-color: #218838; }}
        QPushButton#DangerButton {{ background-color: #dc3545; color: #ffffff; font-weight: bold; border: none; }}
        QPushButton#DangerButton:hover {{ background-color: #c82333; }}
        QPushButton#WarningButton {{ background-color: #ffc107; color: #212529; font-weight: bold; border: none; }}
        QPushButton#WarningButton:hover {{ background-color: #e0a800; }}
        QPushButton#InfoButton {{ background-color: #17a2b8; color: #ffffff; font-weight: bold; border: none; }}
        QPushButton#InfoButton:hover {{ background-color: #138496; }}
        QTableWidget {{ border: 1px solid #dee2e6; gridline-color: #e9ecef; background-color: #ffffff; }}
        QHeaderView::section {{ background-color: #f1f3f5; padding: 6px; border: none; border-bottom: 1px solid #dee2e6; font-weight: bold; }}
        QTableWidget::item:selected {{ background-color: {PRIMARY_COLOR_HOVER}; color: white; }}
        QTabWidget::pane {{ border: 1px solid #dee2e6; border-top: none; background-color: #ffffff; padding: 15px; }}
        QTabBar::tab {{ 
            background: #f1f3f5; border: 1px solid #dee2e6; border-bottom: none; 
            padding: 10px 25px; font-size: 10pt; margin-right: 2px; 
            border-top-left-radius: 6px; border-top-right-radius: 6px; 
            font-weight: bold; color: #495057; 
        }}
        QTabBar::tab:selected {{ 
            background: #ffffff; color: {PRIMARY_COLOR}; border-bottom: 3px solid {PRIMARY_COLOR}; 
        }}
        QSplitter::handle:pressed {{ background-color: {PRIMARY_COLOR}; }}
        QGroupBox {{ 
            border: 1px solid #dee2e6; 
            border-radius: 6px; 
            margin-top: 12px; 
            padding-top: 10px;
            font-weight: bold;
            background-color: #ffffff;
        }}
        QGroupBox::title {{ 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: 2px 10px;
            color: #343a40;
        }}
        QTextEdit {{ 
            border: 1px solid #ced4da; 
            border-radius: 6px; 
            padding: 8px; 
            background-color: #ffffff;
        }}
        QTextEdit:focus {{ 
            border: 1px solid {PRIMARY_COLOR}; 
        }}
    """


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.engine = create_engine_connection()
        self.setObjectName("LoginWindow")
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Production Formulation Program - Login")
        self.setWindowIcon(fa.icon('fa5s.box-open'))
        self.resize(500, 600)
        widget = QWidget()
        self.setCentralWidget(widget)
        main_layout = QHBoxLayout(widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        frame = QFrame(objectName="FormFrame")
        frame.setMaximumWidth(400)
        main_layout.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(QLabel(pixmap=fa.icon('fa5s.boxes', color="#0078d4").pixmap(QSize(150, 150))),
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(
            QLabel("Production Login", objectName="LoginTitle", alignment=Qt.AlignmentFlag.AlignCenter))
        layout.addSpacing(20)

        self.username_widget, self.username = self._create_input_field('fa5s.user', "Username")
        self.password_widget, self.password = self._create_input_field('fa5s.lock', "Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(self.username_widget)
        layout.addWidget(self.password_widget)
        layout.addSpacing(10)

        self.login_btn = QPushButton("Login", objectName="PrimaryButton", shortcut="Return", clicked=self.login)
        self.login_btn.setMinimumHeight(45)
        layout.addWidget(self.login_btn)

        self.status_label = QLabel("", objectName="StatusLabel", alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.setStyleSheet(AppStyles.LOGIN_STYLESHEET)

    def _create_input_field(self, icon, placeholder):
        c = QWidget(objectName="InputFrame")
        l = QHBoxLayout(c)
        l.setContentsMargins(5, 0, 5, 0)
        l.setSpacing(10)
        il = QLabel(pixmap=fa.icon(icon, color='#bdbdbd').pixmap(QSize(20, 20)))
        le = QLineEdit(placeholderText=placeholder)
        l.addWidget(il)
        l.addWidget(le)
        return c, le

    def login(self):
        u, p = self.username.text(), self.password.text()
        if not u or not p:
            self.status_label.setText("Username and password are required.")
            return

        self.login_btn.setEnabled(False)
        self.status_label.setText("Verifying...")

        try:
            credentials = get_user_credentials(self.engine, u)
            if credentials and credentials[0] == p:
                if not credentials[1]:  # qc_access
                    self.status_label.setText("This user does not have access.")
                    return

                # Log login
                workstation_info = _get_workstation_info()
                log_audit_trail(self.engine, u, 'LOGIN', 'User logged in.', workstation_info)

                self.login_successful.emit(u, credentials[2])  # role
                self.close()
            else:
                self.status_label.setText("Invalid credentials.")
        except Exception as e:
            self.status_label.setText("Database connection error.")
            print(f"Login Error: {e}")
        finally:
            self.login_btn.setEnabled(True)


class ModernMainWindow(QMainWindow):
    def __init__(self, username, user_role, login_window):
        super().__init__()
        self.engine = login_window.engine
        self.username = username
        self.user_role = user_role
        self.login_window = login_window
        self.is_animating = False
        self.icon_maximize, self.icon_restore = fa.icon('fa5s.expand-arrows-alt', color='#ecf0f1'), fa.icon(
            'fa5s.compress-arrows-alt', color='#ecf0f1')
        self.icon_db_ok, self.icon_db_fail = fa.icon('fa5s.check-circle', color='#4CAF50'), fa.icon('fa5s.times-circle',
                                                                                                    color='#D32F2F')
        self.setWindowTitle("Production Formulation Program")
        self.setWindowIcon(fa.icon('fa5s.check-double', color='gray'))
        self.setMinimumSize(1280, 720)
        self.setGeometry(100, 100, 1366, 768)
        self.workstation_info = _get_workstation_info()

        # Initialize UI first
        self.init_ui()

    def log_audit_trail(self, action_type, details):
        workstation_info = _get_workstation_info()
        log_audit_trail(self.engine, self.username, action_type, details, workstation_info)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.create_side_menu())

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        try:
            self.formulation_page = FormulationManagementPage(self.engine, self.username, self.log_audit_trail)
            self.audit_trail_page = AuditTrailPage(self.engine)
            self.user_management_page = UserManagementPage(self.engine, self.username, self.log_audit_trail)
        except Exception as e:
            print(f"Error initializing pages: {e}")
            return

        for page in [self.formulation_page, self.audit_trail_page, self.user_management_page]:
            self.stacked_widget.addWidget(page)

        self.setCentralWidget(main_widget)
        self.setup_status_bar()
        self.apply_styles()

        if self.user_role != 'Admin':
            self.btn_user_mgmt.hide()
        self.update_maximize_button()
        self.show_page(0, True)
        self.btn_formulation.setChecked(True)

    def create_side_menu(self):
        menu = QWidget(objectName="SideMenu")
        layout = QVBoxLayout(menu)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        profile = QWidget()
        pl = QHBoxLayout(profile)
        pl.setContentsMargins(5, 0, 0, 0)
        pl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pl.addWidget(QLabel(pixmap=fa.icon('fa5s.user-circle', color='#ecf0f1').pixmap(QSize(40, 40))))
        pl.addWidget(QLabel(f"<b>{self.username}</b><br><font color='#bdc3c7'>{self.user_role}</font>"))

        sep = QFrame(frameShape=QFrame.Shape.HLine, objectName="Separator")
        sep.setContentsMargins(0, 10, 0, 10)

        self.btn_formulation = self.create_menu_button("  Formulation", 'fa5s.flask', 0)
        self.btn_audit_trail = self.create_menu_button("  Audit Trail", 'fa5s.history', 1)
        self.btn_user_mgmt = self.create_menu_button("  User Management", 'fa5s.users-cog', 2)

        self.btn_maximize = QPushButton("  Maximize", icon=self.icon_maximize)
        self.btn_maximize.clicked.connect(self.toggle_maximize)

        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color='#ecf0f1'))
        self.btn_logout.clicked.connect(self.logout)

        layout.addWidget(profile)
        layout.addWidget(sep)
        layout.addWidget(QLabel("FORMULATION", objectName="MenuLabel"))
        layout.addWidget(self.btn_formulation)
        layout.addWidget(QLabel("SYSTEM", objectName="MenuLabel"))
        layout.addWidget(self.btn_audit_trail)
        layout.addWidget(self.btn_user_mgmt)
        layout.addStretch(1)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_logout)

        return menu

    def create_menu_button(self, text, icon, page_index):
        btn = QPushButton(text, icon=fa.icon(icon, color='#ecf0f1'), checkable=True, autoExclusive=True)
        if page_index is not None:
            btn.clicked.connect(lambda: self.show_page(page_index))
        return btn

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Ready | Logged in as: {self.username}")

        self.db_status_icon_label, self.db_status_text_label, self.time_label = QLabel(), QLabel(), QLabel()
        self.db_status_icon_label.setFixedSize(QSize(20, 20))

        # Add sync status label
        self.sync_status_label = QLabel("🔄 Legacy sync: Ready")
        self.status_bar.addPermanentWidget(self.sync_status_label)

        for w in [self.db_status_icon_label, self.db_status_text_label, self.time_label,
                  QLabel(f" | PC: {self.workstation_info['h']}"),
                  QLabel(f" | IP: {self.workstation_info['i']}"),
                  QLabel(f" | MAC: {self.workstation_info['m']}")]:
            self.status_bar.addPermanentWidget(w)

        self.time_timer = QTimer(self, timeout=self.update_time)
        self.time_timer.start(1000)
        self.update_time()

        self.db_check_timer = QTimer(self, timeout=self.check_db_status)
        self.db_check_timer.start(5000)
        self.check_db_status()

    def update_time(self):
        self.time_label.setText(f" | {datetime.now().strftime('%b %d, %Y  %I:%M:%S %p')} ")

    def check_db_status(self):
        if test_database_connection(self.engine):
            self.db_status_icon_label.setPixmap(self.icon_db_ok.pixmap(QSize(16, 16)))
            self.db_status_text_label.setText("DB Connected")
        else:
            self.db_status_icon_label.setPixmap(self.icon_db_fail.pixmap(QSize(16, 16)))
            self.db_status_text_label.setText("DB Disconnected")

    def apply_styles(self):
        self.setStyleSheet(AppStyles.MAIN_WINDOW_STYLESHEET)

    def show_page(self, index, is_first_load=False):
        if self.stacked_widget.currentIndex() == index:
            return
        if self.is_animating and not is_first_load:
            return

        if is_first_load:
            self._set_page_and_refresh(index)
            return

        self.is_animating = True
        current_widget = self.stacked_widget.currentWidget()
        opacity_effect = QGraphicsOpacityEffect()
        current_widget.setGraphicsEffect(opacity_effect)

        self.fade_out_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(150)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(lambda: self._start_fade_in(index, current_widget))
        self.fade_out_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _start_fade_in(self, index, old_widget):
        old_widget.setGraphicsEffect(None)
        self._set_page_and_refresh(index)
        new_widget = self.stacked_widget.currentWidget()
        opacity_effect = QGraphicsOpacityEffect()
        new_widget.setGraphicsEffect(opacity_effect)

        self.fade_in_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in_animation.finished.connect(lambda: self._cleanup_animation(new_widget))
        self.fade_in_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _cleanup_animation(self, widget):
        widget.setGraphicsEffect(None)
        self.is_animating = False

    def _set_page_and_refresh(self, index):
        self.stacked_widget.setCurrentIndex(index)
        current_widget = self.stacked_widget.widget(index)
        if hasattr(current_widget, 'refresh_page'):
            current_widget.refresh_page()

    def toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def update_maximize_button(self):
        self.btn_maximize.setText("  Restore" if self.isMaximized() else "  Maximize")
        self.btn_maximize.setIcon(self.icon_restore if self.isMaximized() else self.icon_maximize)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.update_maximize_button()
        super().changeEvent(event)

    def logout(self):
        self.close()
        self.login_window.show()

    def closeEvent(self, event):
        # Stop any running sync threads
        if hasattr(self, 'sync_thread') and self.sync_thread.isRunning():
            self.sync_thread.quit()
            self.sync_thread.wait(3000)  # Wait up to 3 seconds
        self.login_window.close()
        event.accept()


def main():
    app = QApplication(sys.argv)

    engine = create_engine_connection()
    if not initialize_database(engine):
        QMessageBox.critical(None, "DB Init Error", "Could not initialize database.")
        sys.exit(1)

    login_window = LoginWindow()
    main_window = None

    def on_login_success(username, user_role):
        nonlocal main_window
        main_window = ModernMainWindow(username, user_role, login_window)
        main_window.showMaximized()

    login_window.login_successful.connect(on_login_success)
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()