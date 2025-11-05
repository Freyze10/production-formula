import sys
import os
from datetime import datetime
from PyQt6.QtCore import (
    QTimer, Qt, QSize, QEvent, QPropertyAnimation, QEasingCurve,
    QAbstractAnimation, pyqtSignal, QCoreApplication
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QMessageBox, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QStatusBar,
    QGraphicsOpacityEffect
)

# --- Page imports ---
try:
    from side_bar.audit_trail import AuditTrailPage
    from side_bar.user_management import UserManagementPage
    from side_bar.formulation import FormulationManagementPage
    from side_bar.production import ProductionManagementPage
    from utils.work_station import _get_workstation_info
    from db.engine_conn import create_engine_connection
    from db.schema import initialize_database, get_user_credentials, log_audit_trail, test_database_connection
except ImportError as e:
    print(f"FATAL: Missing required module import: {e}")
    sys.exit(1)

try:
    import qtawesome as fa
except ImportError:
    print("FATAL ERROR: The 'qtawesome' library is required. Please install it using: pip install qtawesome")
    sys.exit(1)


class AppStyles:
    """Modern, visually appealing stylesheet with enhanced readability."""
    PRIMARY_COLOR = "#4F46E5"
    PRIMARY_COLOR_HOVER = "#4338CA"
    PRIMARY_COLOR_LIGHT = "#818CF8"
    ACCENT_COLOR = "#06B6D4"
    SUCCESS_COLOR = "#10B981"
    WARNING_COLOR = "#F59E0B"
    DANGER_COLOR = "#EF4444"
    INFO_COLOR = "#3B82F6"

    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F9FAFB"
    BG_TERTIARY = "#F3F4F6"
    BG_DARK = "#1F2937"
    BG_DARKER = "#111827"

    TEXT_PRIMARY = "#111827"
    TEXT_SECONDARY = "#6B7280"
    TEXT_TERTIARY = "#9CA3AF"
    TEXT_LIGHT = "#F9FAFB"

    BORDER_COLOR = "#E5E7EB"
    BORDER_FOCUS = PRIMARY_COLOR

    SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    SHADOW_XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"

    LOGIN_STYLESHEET = f"""
        #LoginWindow, #FormFrame {{ 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {BG_SECONDARY}, stop:1 #E0E7FF);
        }}
        QWidget {{ 
            font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif; 
            font-size: 10pt; 
            color: {TEXT_PRIMARY};
        }}
        #FormFrame {{ background-color: {BG_PRIMARY}; border-radius: 16px; padding: 20px; }}
        #LoginTitle {{ font-size: 24pt; font-weight: 600; color: {TEXT_PRIMARY}; letter-spacing: -0.5px; }}
        #InputFrame {{ background-color: {BG_SECONDARY}; border: 2px solid {BORDER_COLOR}; border-radius: 12px; padding: 8px 12px; }}
        #InputFrame:focus-within {{ border: 2px solid {PRIMARY_COLOR}; background-color: {BG_PRIMARY}; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }}
        QLineEdit {{ border: none; background-color: transparent; padding: 8px 4px; font-size: 11pt; color: {TEXT_PRIMARY}; }}
        QLineEdit::placeholder {{ color: {TEXT_TERTIARY}; }}
        QPushButton#PrimaryButton {{ 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_COLOR_HOVER});
            color: {TEXT_LIGHT}; border-radius: 12px; padding: 12px 24px; font-weight: 600; font-size: 11pt; border: none;
        }}
        QPushButton#PrimaryButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PRIMARY_COLOR_HOVER}, stop:1 #3730A3); }}
        QPushButton#PrimaryButton:pressed {{ padding: 13px 24px 11px 24px; }}
        QPushButton#PrimaryButton:disabled {{ background-color: {TEXT_TERTIARY}; color: {BG_SECONDARY}; }}
        #StatusLabel {{ color: {DANGER_COLOR}; font-size: 10pt; font-weight: 500; }}
    """

    MAIN_WINDOW_STYLESHEET = f"""
        QMainWindow, QStackedWidget > QWidget {{ background-color: {BG_SECONDARY}; }}
        QWidget {{ font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif; font-size: 9.5pt; color: {TEXT_PRIMARY}; }}
        QStatusBar, QStatusBar QLabel {{ background-color: {BG_PRIMARY}; font-size: 9pt; color: {TEXT_SECONDARY}; border-top: 1px solid {BORDER_COLOR}; padding: 4px 8px; }}
        QWidget#SideMenu {{ 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_DARKER}, stop:1 {BG_DARK});
            color: {TEXT_LIGHT}; width: 240px; border-right: 1px solid rgba(255, 255, 255, 0.05);
        }}
        #SideMenu QLabel {{ color: {TEXT_LIGHT}; font-family: "Segoe UI", sans-serif; font-size: 10pt; }}
        #SideMenu #MenuLabel {{ font-size: 9pt; font-weight: 700; color: {TEXT_TERTIARY}; padding: 12px 16px 6px 16px; margin-top: 12px; letter-spacing: 1.2px; text-transform: uppercase; }}
        #SideMenu QPushButton {{ 
            background-color: transparent; color: {TEXT_LIGHT}; border: none; padding: 12px 16px; text-align: left; 
            font-size: 10.5pt; font-weight: 500; border-radius: 10px; margin: 2px 8px; transition: all 0.2s ease;
        }}
        #SideMenu QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.08); padding-left: 20px; }}
        #SideMenu QPushButton:checked {{ 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_COLOR_LIGHT});
            font-weight: 600; color: {TEXT_LIGHT};
        }}
        QFrame#Separator {{ background-color: rgba(255, 255, 255, 0.1); height: 1px; margin: 8px 0px; }}
        QFormLayout QLabel, QGridLayout QLabel, QGroupBox {{ font-weight: 600; color: {TEXT_PRIMARY}; font-size: 9.5pt; }}
        QLineEdit, QComboBox, QDateEdit, QTextEdit {{ 
            border: 1.5px solid {BORDER_COLOR}; padding: 6px 8px; border-radius: 8px; background-color: {BG_PRIMARY}; 
            min-height: 20px; min-width: 90px; color: {TEXT_PRIMARY}; selection-background-color: {PRIMARY_COLOR_LIGHT};
        }}
        QComboBox {{ padding: 6px; }}
        QDateEdit {{ min-width: 90px; padding-right: 4px; }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{ 
            border: 1.5px solid {PRIMARY_COLOR}; background-color: {BG_PRIMARY}; outline: none;
        }}
        QLineEdit:read-only {{ background-color: {BG_TERTIARY}; color: {TEXT_SECONDARY}; border: 1.5px solid {BORDER_COLOR}; }}
        QLineEdit::placeholder, QTextEdit::placeholder {{ color: {TEXT_TERTIARY}; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border-left: 1.5px solid {BORDER_COLOR}; border-top-right-radius: 8px; border-bottom-right-radius: 8px; background-color: {BG_TERTIARY}; }}
        QComboBox QAbstractItemView {{ border: 1.5px solid {BORDER_COLOR}; border-radius: 8px; background-color: {BG_PRIMARY}; selection-background-color: {PRIMARY_COLOR_LIGHT}; selection-color: {TEXT_PRIMARY}; padding: 4px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 2px solid {BORDER_COLOR}; background-color: {BG_PRIMARY}; }}
        QCheckBox::indicator:hover {{ border: 2px solid {PRIMARY_COLOR}; }}
        QCheckBox::indicator:checked {{ background-color: {PRIMARY_COLOR}; border: 2px solid {PRIMARY_COLOR}; }}
        QPushButton {{ padding: 9px 18px; font-size: 9.5pt; border: 1.5px solid {BORDER_COLOR}; border-radius: 8px; background-color: {BG_PRIMARY}; color: {TEXT_PRIMARY}; font-weight: 500; }}
        QPushButton:hover {{ background-color: {BG_TERTIARY}; border-color: {TEXT_TERTIARY}; }}
        QPushButton:pressed {{ background-color: {BORDER_COLOR}; }}
        QPushButton#PrimaryButton {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_COLOR_HOVER}); color: {TEXT_LIGHT}; font-weight: 600; border: none; }}
        QPushButton#PrimaryButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PRIMARY_COLOR_LIGHT}, stop:1 {PRIMARY_COLOR}); }}
        QPushButton#SecondaryButton {{ background-color: {TEXT_SECONDARY}; color: {TEXT_LIGHT}; font-weight: 600; border: none; }}
        QPushButton#SecondaryButton:hover {{ background-color: {TEXT_PRIMARY}; }}
        QPushButton#SuccessButton {{ background-color: {SUCCESS_COLOR}; color: {TEXT_LIGHT}; font-weight: 600; border: none; }}
        QPushButton#SuccessButton:hover {{ background-color: #059669; }}
        QPushButton#DangerButton {{ background-color: {DANGER_COLOR}; color: {TEXT_LIGHT}; font-weight: 600; border: none; }}
        QPushButton#DangerButton:hover {{ background-color: #DC2626; }}
        QPushButton#WarningButton {{ background-color: {WARNING_COLOR}; color: {TEXT_PRIMARY}; font-weight: 600; border: none; }}
        QPushButton#WarningButton:hover {{ background-color: #B45309; }}
        QPushButton#InfoButton {{ background-color: {INFO_COLOR}; color: {TEXT_LIGHT}; font-weight: 600; border: none; }}
        QPushButton#InfoButton:hover {{ background-color: #2563EB; }}
        QTableWidget {{ border: 1px solid {BORDER_COLOR}; gridline-color: {BORDER_COLOR}; background-color: {BG_PRIMARY}; border-radius: 8px; alternate-background-color: {BG_SECONDARY}; }}
        QHeaderView::section {{ background-color: {BG_TERTIARY}; padding: 6px 4px; border: none; border-bottom: 2px solid {BORDER_COLOR}; border-right: 1px solid {BORDER_COLOR}; font-weight: 600; text-transform: uppercase; font-size: 8.5pt; letter-spacing: 0.5px; }}
        QHeaderView::section:first {{ border-top-left-radius: 8px; }}
        QHeaderView::section:last {{ border-top-right-radius: 8px; border-right: none; }}
        QTableWidget::item {{ padding: 8px; border: none; color: {TEXT_SECONDARY}; }}
        QTableWidget::item:selected {{ background-color: {PRIMARY_COLOR_LIGHT}; color: {TEXT_PRIMARY}; }}
        QTableWidget::item:hover {{ background-color: rgba(79, 70, 229, 0.08); }}
        QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; border-top: none; background-color: {BG_PRIMARY}; padding: 16px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }}
        QTabBar::tab {{ background: {BG_TERTIARY}; border: 1px solid {BORDER_COLOR}; border-bottom: none; padding: 12px 28px; font-size: 10pt; margin-right: 3px; border-top-left-radius: 10px; border-top-right-radius: 10px; font-weight: 500; color: {TEXT_SECONDARY}; }}
        QTabBar::tab:hover {{ background: {BG_SECONDARY}; color: {TEXT_PRIMARY}; }}
        QTabBar::tab:selected {{ background: {BG_PRIMARY}; color: {PRIMARY_COLOR}; border-bottom: 3px solid {PRIMARY_COLOR}; font-weight: 600; padding-top: 11px; }}
        QGroupBox {{ border: none; border-radius: 12px; margin-top: 20px; padding: 14px 16px 14px 16px; font-weight: 600; background-color: {BG_SECONDARY}; font-size: 10.5pt; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 6px 14px; color: {PRIMARY_COLOR}; background-color: transparent; font-weight: 700; left: 8px; top: -8px; letter-spacing: 0.3px; }}
        QTextEdit {{ border: 1.5px solid {BORDER_COLOR}; border-radius: 8px; padding: 6px; background-color: {BG_PRIMARY}; line-height: 2.5; }}
        QTextEdit:focus {{ border: 1.5px solid {PRIMARY_COLOR}; }}
        QScrollBar:vertical {{ border: none; background: {BG_TERTIARY}; width: 12px; border-radius: 6px; margin: 0px; }}
        QScrollBar::handle:vertical {{ background: {TEXT_TERTIARY}; border-radius: 6px; min-height: 30px; }}
        QScrollBar::handle:vertical:hover {{ background: {TEXT_SECONDARY}; }}
        QScrollBar:horizontal {{ border: none; background: {BG_TERTIARY}; height: 12px; border-radius: 6px; margin: 0px; }}
        QScrollBar::handle:horizontal {{ background: {TEXT_TERTIARY}; border-radius: 6px; min-width: 20px; }}
        QScrollBar::handle:horizontal:hover {{ background: {TEXT_SECONDARY}; }}
        QSplitter::handle {{ background-color: {BORDER_COLOR}; }}
        QSplitter::handle:hover {{ background-color: {PRIMARY_COLOR}; }}
        QSplitter::handle:pressed {{ background-color: {PRIMARY_COLOR_HOVER}; }}
        QFrame#ContentCard {{ background-color: {BG_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; padding: 16px; }}
        QFrame#HeaderCard {{ background-color: {BG_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; padding: 12px 16px; }}
    """


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet(
            f"""
            background: {AppStyles.BG_PRIMARY};
            border-radius: 16px;
            """
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # App Logo / Icon
        icon_label = QLabel()
        icon_label.setPixmap(fa.icon('fa5s.box-open', color=AppStyles.PRIMARY_COLOR).pixmap(QSize(80, 80)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Initializing Application")
        title.setStyleSheet(
            f"font-size: 20pt; font-weight: 600; color: {AppStyles.PRIMARY_COLOR}; background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        self.subtitle = QLabel("Loading modules...")
        self.subtitle.setStyleSheet(
            f"font-size: 12pt; color: {AppStyles.TEXT_SECONDARY}; background: transparent;"
        )
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Static Dots Label (no animation)
        self.dots_label = QLabel("●●●")
        self.dots_label.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {AppStyles.PRIMARY_COLOR}; background: transparent;"
        )
        self.dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.dots_label)

    def stop(self):
        self.hide()


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.engine = create_engine_connection()
        self.loading = None
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
        layout.addWidget(QLabel("Production Login", objectName="LoginTitle", alignment=Qt.AlignmentFlag.AlignCenter))
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
                if not credentials[1]:
                    self.status_label.setText("This user does not have access.")
                    return

                workstation_info = _get_workstation_info()
                log_audit_trail(self.engine, u, 'LOGIN', 'User logged in.', workstation_info)

                self.login_successful.emit(u, credentials[2])
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
        self.setMinimumSize(1400, 720)
        self.setGeometry(100, 100, 1366, 768)
        self.workstation_info = _get_workstation_info()

        # Initialize pages to None
        self.formulation_page = None
        self.production_page = None
        self.audit_trail_page = None
        self.user_management_page = None

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

        self.setCentralWidget(main_widget)
        self.setup_status_bar()
        self.apply_styles()

    def _initialize_pages(self):
        try:
            print("Initializing pages...")
            self.formulation_page = FormulationManagementPage(self.engine, self.username, self.user_role,
                                                              self.log_audit_trail)
            try:
                self.production_page = ProductionManagementPage(self.engine, self.username, self.user_role,
                                                                self.log_audit_trail)
            except Exception as e:
                print(f"PRODUCTION PAGE INIT ERROR: {e}")

            self.audit_trail_page = AuditTrailPage(self.engine)
            self.user_management_page = UserManagementPage(self.engine, self.username, self.log_audit_trail)

            for page in [self.formulation_page, self.production_page, self.audit_trail_page, self.user_management_page]:
                self.stacked_widget.addWidget(page)

            if self.user_role != 'Admin':
                self.btn_user_mgmt.hide()
                if self.stacked_widget.widget(0) == self.user_management_page:
                    self.show_page(0, True)
                else:
                    self.show_page(0, True)
            else:
                self.show_page(0, True)

            self.btn_formulation.setChecked(True)
            print("All pages loaded.")
        except Exception as e:
            print(f"PAGE INIT ERROR: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load pages: {e}")

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
        self.btn_production = self.create_menu_button("  Production", 'fa5s.industry', 1)
        self.btn_audit_trail = self.create_menu_button("  Audit Trail", 'fa5s.history', 2)
        self.btn_user_mgmt = self.create_menu_button("  User Management", 'fa5s.users-cog', 3)

        self.btn_maximize = QPushButton("  Maximize", icon=self.icon_maximize)
        self.btn_maximize.clicked.connect(self.toggle_maximize)

        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color='#ecf0f1'))
        self.btn_logout.clicked.connect(self.logout)

        layout.addWidget(profile)
        layout.addWidget(sep)
        layout.addWidget(QLabel("FORMULATION", objectName="MenuLabel"))
        layout.addWidget(self.btn_formulation)
        layout.addWidget(QLabel("PRODUCTION", objectName="MenuLabel"))
        layout.addWidget(self.btn_production)
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
        self.db_status_icon_label.setFixedSize(QSize(36, 30))
        self.db_status_icon_label.setScaledContents(True)

        self.sync_status_label = QLabel("Legacy sync: Ready")
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
            self.db_status_icon_label.setPixmap(self.icon_db_ok.pixmap(QSize(30, 30)))
            self.db_status_text_label.setText("DB Connected")
        else:
            self.db_status_icon_label.setPixmap(self.icon_db_fail.pixmap(QSize(30, 30)))
            self.db_status_text_label.setText("DB Disconnected")

    def apply_styles(self):
        self.setStyleSheet(AppStyles.MAIN_WINDOW_STYLESHEET)

    def show_page(self, index, is_first_load=False):
        if self.formulation_page is None and index != 0 and not is_first_load:
            return

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

        # 1. Show Loading Overlay immediately
        loading = LoadingOverlay()
        screen = QApplication.primaryScreen().availableGeometry()

        # Center the loading screen
        loading.resize(500, 380)
        loading.move(screen.center().x() - loading.width() // 2, screen.center().y() - loading.height() // 2)
        loading.show()
        QCoreApplication.processEvents()  # Ensure the overlay is painted

        # 2. Create Main Window (fast operation: creates UI shell)
        main_window = ModernMainWindow(username, user_role, login_window)

        # 3. Use QTimer to allow the loading overlay to render first, then start heavy work
        def start_loading():
            try:
                # Perform the heavy work (instantiate all QWidgets and load data)
                main_window._initialize_pages()

                # 4. Hide loading overlay
                loading.stop()
                loading.deleteLater()

                # 5. Show the main window fully loaded
                main_window.showMaximized()
                main_window.activateWindow()
                main_window.raise_()

            except Exception as e:
                loading.stop()
                loading.deleteLater()
                QMessageBox.critical(None, "Init Error", f"Failed to load main application components: {e}")
                login_window.show()

        # Delay by 50ms to let the loading overlay paint itself first
        QTimer.singleShot(50, start_loading)

    login_window.login_successful.connect(on_login_success)
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()