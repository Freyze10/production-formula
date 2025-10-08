# main.py
# FINAL VERIFIED VERSION

import sys
import os
import re
from datetime import datetime
import socket
import uuid
import dbfread
import time

from sqlalchemy import create_engine, text

try:
    import qtawesome as fa
except ImportError:
    print("FATAL ERROR: The 'qtawesome' library is required. Please install it using: pip install qtawesome")
    sys.exit(1)

from PyQt6.QtCore import (Qt, pyqtSignal, QSize, QEvent, QTimer, QThread, QObject, QPropertyAnimation, QEasingCurve,
                          QAbstractAnimation)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
                             QMessageBox, QVBoxLayout, QHBoxLayout, QStackedWidget,
                             QFrame, QStatusBar, QDialog)
from PyQt6.QtGui import QFont, QMovie

# --- All page imports are correct ---
from fg_endorsement import FGEndorsementPage
from audit_trail import AuditTrailPage
from user_management import UserManagementPage

# --- CONFIGURATION ---
DB_CONFIG = {"host": "localhost", "port": 5433, "dbname": "db_formula", "user": "postgres", "password": "password"}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
PRODUCTION_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod01.dbf')
db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)


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
        QLineEdit, QComboBox, QDateEdit {{ border: 1px solid #ced4da; padding: 8px; border-radius: 6px; background-color: #ffffff; min-height: 20px; }}
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
    """


class SyncWorker(QObject):
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            dbf = dbfread.DBF(PRODUCTION_DBF_PATH, load=True, encoding='latin1')
            if 'T_LOTNUM' not in dbf.field_names:
                self.finished.emit(False, "Sync Error: Required column 'T_LOTNUM' not found.")
                return
            recs = [{"lot": str(r.get('T_LOTNUM', '')).strip().upper(), "code": str(r.get('T_PRODCODE', '')).strip(),
                     "cust": str(r.get('T_CUSTOMER', '')).strip(),
                     "fid": str(int(r.get('T_FID'))) if r.get('T_FID') is not None else '',
                     "op": str(r.get('T_OPER', '')).strip(), "sup": str(r.get('T_SUPER', '')).strip()} for r in
                    dbf.records if str(r.get('T_LOTNUM', '')).strip()]
            if not recs:
                self.finished.emit(True, "Sync Info: No new records found in DBF file to sync.")
                return
            with engine.connect() as conn:
                with conn.begin(): conn.execute(text(
                    "INSERT INTO legacy_production(lot_number,prod_code,customer_name,formula_id,operator,supervisor,last_synced_on) VALUES(:lot,:code,:cust,:fid,:op,:sup,NOW()) ON CONFLICT(lot_number) DO UPDATE SET prod_code=EXCLUDED.prod_code, customer_name=EXCLUDED.customer_name, formula_id=EXCLUDED.formula_id, operator=EXCLUDED.operator, supervisor=EXCLUDED.supervisor, last_synced_on=NOW()"),
                                                recs)
            self.finished.emit(True, f"Production sync complete.\n{len(recs)} records processed.")
        except dbfread.DBFNotFound:
            self.finished.emit(False, f"File Not Found: Production DBF not found at:\n{PRODUCTION_DBF_PATH}")
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred during sync:\n{e}")


def initialize_database():
    print("Initializing database schema...")
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                connection.execute(text(
                    "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, qc_access BOOLEAN DEFAULT TRUE, role TEXT DEFAULT 'Editor');"))
                connection.execute(text(
                    "CREATE TABLE IF NOT EXISTS qc_audit_trail (id SERIAL PRIMARY KEY, timestamp TIMESTAMP, username TEXT, action_type TEXT, details TEXT, hostname TEXT, ip_address TEXT, mac_address TEXT);"))
                connection.execute(text(
                    "CREATE TABLE IF NOT EXISTS legacy_production (lot_number TEXT PRIMARY KEY, prod_code TEXT, customer_name TEXT, formula_id TEXT, operator TEXT, supervisor TEXT, last_synced_on TIMESTAMP);"))
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_legacy_production_lot_number ON legacy_production (lot_number);"))
                connection.execute(
                    text("CREATE TABLE IF NOT EXISTS endorsers (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL);"))
                connection.execute(text(
                    "CREATE TABLE IF NOT EXISTS endorsement_remarks (id SERIAL PRIMARY KEY, remark_text TEXT UNIQUE NOT NULL);"))
                endorsement_columns = "system_ref_no TEXT NOT NULL, form_ref_no TEXT, date_endorsed DATE, category TEXT, product_code TEXT, lot_number TEXT, quantity_kg NUMERIC(15, 6), weight_per_lot NUMERIC(15, 6), bag_no TEXT, status TEXT, endorsed_by TEXT, remarks TEXT, encoded_by TEXT, encoded_on TIMESTAMP, edited_by TEXT, edited_on TIMESTAMP"
                connection.execute(text(
                    f"CREATE TABLE IF NOT EXISTS fg_endorsements_primary (id SERIAL PRIMARY KEY, {endorsement_columns}, UNIQUE(system_ref_no));"))
                connection.execute(text(
                    f"CREATE TABLE IF NOT EXISTS fg_endorsements_secondary (id SERIAL PRIMARY KEY, system_ref_no TEXT, lot_number TEXT, quantity_kg NUMERIC(15, 6), product_code TEXT, status TEXT, bag_no TEXT, endorsed_by TEXT);"))
                connection.execute(text(
                    f"CREATE TABLE IF NOT EXISTS fg_endorsements_excess (id SERIAL PRIMARY KEY, system_ref_no TEXT, lot_number TEXT, quantity_kg NUMERIC(15, 6), product_code TEXT, status TEXT, bag_no TEXT, endorsed_by TEXT);"))
                user_insert_query = text(
                    "INSERT INTO users (username, password, role) VALUES (:user, :pwd, :role) ON CONFLICT (username) DO NOTHING;")
                connection.execute(user_insert_query, [{"user": "admin", "pwd": "itadmin", "role": "Admin"},
                                                       {"user": "itsup", "pwd": "itsup", "role": "Editor"}])
                transaction.commit()
        print("Database initialized successfully.")
    except Exception as e:
        QApplication(sys.argv);
        QMessageBox.critical(None, "DB Init Error", f"Could not init DB: {e}");
        sys.exit(1)


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setObjectName("LoginWindow")
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Finished Goods Program - Login")
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
            QLabel("Finished Goods Login", objectName="LoginTitle", alignment=Qt.AlignmentFlag.AlignCenter))
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
        c = QWidget(objectName="InputFrame");
        l = QHBoxLayout(c);
        l.setContentsMargins(5, 0, 5, 0);
        l.setSpacing(10);
        il = QLabel(pixmap=fa.icon(icon, color='#bdbdbd').pixmap(QSize(20, 20)));
        le = QLineEdit(placeholderText=placeholder);
        l.addWidget(il);
        l.addWidget(le);
        return c, le

    def login(self):
        u, p = self.username.text(), self.password.text()
        if not u or not p:
            self.status_label.setText("Username and password are required.");
            return
        self.login_btn.setEnabled(False);
        self.status_label.setText("Verifying...")
        try:
            with engine.connect() as c:
                with c.begin():
                    res = c.execute(text("SELECT password, qc_access, role FROM users WHERE username=:u"),
                                    {"u": u}).fetchone()
                    if res and res[0] == p:
                        if not res[1]:
                            self.status_label.setText("This user does not have access.");
                            return
                        c.execute(text(
                            "INSERT INTO qc_audit_trail(timestamp, username, action_type, details, hostname, ip_address, mac_address) VALUES (NOW(), :u, 'LOGIN', 'User logged in.', :h, :i, :m)"),
                                  {"u": u, **self._get_workstation_info()})
                        self.login_successful.emit(u, res[2]);
                        self.close()
                    else:
                        self.status_label.setText("Invalid credentials.")
        except Exception as e:
            self.status_label.setText("Database connection error."); print(f"Login Error: {e}")
        finally:
            self.login_btn.setEnabled(True)

    def _get_workstation_info(self):
        try:
            h, i = socket.gethostname(), socket.gethostbyname(socket.gethostname())
        except:
            h, i = 'Unknown', 'N/A'
        try:
            m = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        except:
            m = 'N/A'
        return {"h": h, "i": i, "m": m}


class ModernMainWindow(QMainWindow):
    def __init__(self, username, user_role, login_window):
        super().__init__()
        self.username, self.user_role, self.login_window = username, user_role, login_window
        self.icon_maximize, self.icon_restore = fa.icon('fa5s.expand-arrows-alt', color='#ecf0f1'), fa.icon(
            'fa5s.compress-arrows-alt', color='#ecf0f1')
        self.icon_db_ok, self.icon_db_fail = fa.icon('fa5s.check-circle', color='#4CAF50'), fa.icon('fa5s.times-circle',
                                                                                                    color='#D32F2F')
        self.setWindowTitle("Finished Goods Program")
        self.setWindowIcon(fa.icon('fa5s.check-double', color='gray'))
        self.setMinimumSize(1280, 720);
        self.setGeometry(100, 100, 1366, 768)
        self.workstation_info = self._get_workstation_info()
        self.animation = None
        self.init_ui()

    def _get_workstation_info(self):
        try:
            h, i = socket.gethostname(), socket.gethostbyname(socket.gethostname())
        except:
            h, i = 'Unknown', 'N/A'
        try:
            m = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        except:
            m = 'N/A'
        return {"h": h, "i": i, "m": m}

    def log_audit_trail(self, action_type, details):
        try:
            log_query = text(
                "INSERT INTO qc_audit_trail (timestamp, username, action_type, details, hostname, ip_address, mac_address) VALUES (NOW(), :u, :a, :d, :h, :i, :m)")
            with engine.connect() as connection:
                with connection.begin(): connection.execute(log_query,
                                                            {"u": self.username, "a": action_type, "d": details,
                                                             **self.workstation_info})
        except Exception as e:
            print(f"CRITICAL: Audit trail error: {e}")

    def init_ui(self):
        main_widget = QWidget();
        main_layout = QHBoxLayout(main_widget);
        main_layout.setContentsMargins(0, 0, 0, 0);
        main_layout.setSpacing(0)
        main_layout.addWidget(self.create_side_menu())
        self.stacked_widget = QStackedWidget();
        main_layout.addWidget(self.stacked_widget)

        # --- FIXED: Instantiate all real pages correctly ---
        self.fg_endorsement_page = FGEndorsementPage(engine, self.username, self.log_audit_trail)
        self.audit_trail_page = AuditTrailPage(engine)
        self.user_management_page = UserManagementPage(engine, self.username, self.log_audit_trail)

        for page in [self.fg_endorsement_page, self.audit_trail_page, self.user_management_page]:
            self.stacked_widget.addWidget(page)

        self.setCentralWidget(main_widget);
        self.setup_status_bar();
        self.apply_styles()
        if self.user_role != 'Admin': self.btn_user_mgmt.hide()
        self.update_maximize_button();
        self.show_page(0, True);
        self.btn_fg_endorsement.setChecked(True)

    def create_side_menu(self):
        menu = QWidget(objectName="SideMenu");
        layout = QVBoxLayout(menu);
        layout.setContentsMargins(10, 20, 10, 10);
        layout.setSpacing(5);
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        profile = QWidget();
        pl = QHBoxLayout(profile);
        pl.setContentsMargins(5, 0, 0, 0);
        pl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pl.addWidget(QLabel(pixmap=fa.icon('fa5s.user-circle', color='#ecf0f1').pixmap(QSize(40, 40))));
        pl.addWidget(QLabel(f"<b>{self.username}</b><br><font color='#bdc3c7'>{self.user_role}</font>"))
        sep = QFrame(frameShape=QFrame.Shape.HLine, objectName="Separator");
        sep.setContentsMargins(0, 10, 0, 10)
        self.btn_fg_endorsement = self.create_menu_button("  FG Endorsement", 'fa5s.file-signature', 0)
        self.btn_sync_prod = QPushButton("  Sync Production DB", icon=fa.icon('fa5s.sync-alt', color='#ecf0f1'));
        self.btn_sync_prod.clicked.connect(self.start_sync_process)
        self.btn_audit_trail = self.create_menu_button("  Audit Trail", 'fa5s.history', 1)
        self.btn_user_mgmt = self.create_menu_button("  User Management", 'fa5s.users-cog', 2)
        self.btn_maximize = QPushButton("  Maximize", icon=self.icon_maximize);
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color='#ecf0f1'));
        self.btn_logout.clicked.connect(self.logout)
        layout.addWidget(profile);
        layout.addWidget(sep)
        layout.addWidget(QLabel("FG MANAGEMENT", objectName="MenuLabel"));
        layout.addWidget(self.btn_fg_endorsement);
        layout.addWidget(self.btn_sync_prod)
        layout.addWidget(QLabel("SYSTEM", objectName="MenuLabel"));
        layout.addWidget(self.btn_audit_trail);
        layout.addWidget(self.btn_user_mgmt)
        layout.addStretch(1);
        layout.addWidget(self.btn_maximize);
        layout.addWidget(self.btn_logout)
        return menu

    def create_menu_button(self, text, icon, page_index):
        btn = QPushButton(text, icon=fa.icon(icon, color='#ecf0f1'), checkable=True, autoExclusive=True)
        btn.clicked.connect(lambda: self.show_page(page_index));
        return btn

    def setup_status_bar(self):
        self.status_bar = QStatusBar();
        self.setStatusBar(self.status_bar);
        self.status_bar.showMessage(f"Ready | Logged in as: {self.username}")
        self.db_status_icon_label, self.db_status_text_label, self.time_label = QLabel(), QLabel(), QLabel();
        self.db_status_icon_label.setFixedSize(QSize(20, 20))
        for w in [self.db_status_icon_label, self.db_status_text_label, self.time_label,
                  QLabel(f" | PC: {self.workstation_info['h']}"), QLabel(f" | IP: {self.workstation_info['i']}"),
                  QLabel(f" | MAC: {self.workstation_info['m']}")]: self.status_bar.addPermanentWidget(w)
        self.time_timer = QTimer(self, timeout=self.update_time);
        self.time_timer.start(1000);
        self.update_time()
        self.db_check_timer = QTimer(self, timeout=self.check_db_status);
        self.db_check_timer.start(5000);
        self.check_db_status()

    def start_sync_process(self):
        reply = QMessageBox.question(self, "Confirm Sync",
                                     "This will sync with the legacy production database. This may take some time. Are you sure you want to proceed?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        self.btn_sync_prod.setEnabled(False);
        self.loading_dialog = self._create_loading_dialog()
        self.sync_thread = QThread();
        self.sync_worker = SyncWorker();
        self.sync_worker.moveToThread(self.sync_thread)
        self.sync_thread.started.connect(self.sync_worker.run);
        self.sync_worker.finished.connect(self.on_sync_finished);
        self.sync_worker.finished.connect(self.sync_thread.quit);
        self.sync_worker.finished.connect(self.sync_worker.deleteLater);
        self.sync_thread.finished.connect(self.sync_thread.deleteLater)
        self.sync_thread.start();
        self.loading_dialog.exec()

    def _create_loading_dialog(self):
        dialog = QDialog(self);
        dialog.setModal(True);
        dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint);
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(dialog);
        frame = QFrame();
        frame.setStyleSheet("background-color: white; border-radius: 15px; padding: 20px;");
        frame_layout = QVBoxLayout(frame)
        loading_label = QLabel();
        movie = QMovie("loading.gif")
        if not movie.isValid():
            loading_label.setText("Loading...")
        else:
            loading_label.setMovie(movie); movie.start()
        message_label = QLabel("Syncing... Please wait.");
        message_label.setStyleSheet("font-size: 11pt;")
        frame_layout.addWidget(loading_label, alignment=Qt.AlignmentFlag.AlignCenter);
        frame_layout.addWidget(message_label, alignment=Qt.AlignmentFlag.AlignCenter);
        layout.addWidget(frame)
        return dialog

    def on_sync_finished(self, success, message):
        self.loading_dialog.close();
        self.btn_sync_prod.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sync Result", message); self.status_bar.showMessage(
                "Production DB synchronized.", 5000)
        else:
            QMessageBox.critical(self, "Sync Result", message); self.status_bar.showMessage("Sync failed.", 5000)

    def update_time(self):
        self.time_label.setText(f" | {datetime.now().strftime('%b %d, %Y  %I:%M:%S %p')} ")

    def check_db_status(self):
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
            self.db_status_icon_label.setPixmap(self.icon_db_ok.pixmap(QSize(16, 16)));
            self.db_status_text_label.setText("DB Connected")
        except:
            self.db_status_icon_label.setPixmap(
                self.icon_db_fail.pixmap(QSize(16, 16))); self.db_status_text_label.setText("DB Disconnected")

    def apply_styles(self):
        self.setStyleSheet(AppStyles.MAIN_WINDOW_STYLESHEET)

    def show_page(self, index, is_first_load=False):
        if self.stacked_widget.currentIndex() == index: return
        if is_first_load or self.animation and self.animation.state() == QAbstractAnimation.State.Running:
            self._set_page_and_refresh(index);
            return
        current_widget = self.stacked_widget.currentWidget()
        self.fade_out_animation = QPropertyAnimation(current_widget, b"windowOpacity");
        self.fade_out_animation.setDuration(150);
        self.fade_out_animation.setStartValue(1.0);
        self.fade_out_animation.setEndValue(0.0);
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(lambda: self._start_fade_in(index));
        self.animation = self.fade_out_animation;
        self.fade_out_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _start_fade_in(self, index):
        self._set_page_and_refresh(index)
        new_widget = self.stacked_widget.currentWidget()
        self.fade_in_animation = QPropertyAnimation(new_widget, b"windowOpacity");
        self.fade_in_animation.setDuration(200);
        self.fade_in_animation.setStartValue(0.0);
        self.fade_in_animation.setEndValue(1.0);
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation = self.fade_in_animation;
        self.fade_in_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # --- FIXED: This single method handles refreshing all pages correctly ---
    def _set_page_and_refresh(self, index):
        """Sets the current page and calls its refresh method if it exists."""
        self.stacked_widget.setCurrentIndex(index)
        current_widget = self.stacked_widget.widget(index)
        if hasattr(current_widget, 'refresh_page'):
            current_widget.refresh_page()

    def toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def update_maximize_button(self):
        self.btn_maximize.setText("  Restore" if self.isMaximized() else "  Maximize"); self.btn_maximize.setIcon(
            self.icon_restore if self.isMaximized() else self.icon_maximize)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange: self.update_maximize_button()
        super().changeEvent(event)

    def logout(self):
        self.close(); self.login_window.show()

    def closeEvent(self, event):
        self.login_window.close(); event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    initialize_database()
    login_window = LoginWindow()
    main_window = None


    def on_login_success(username, user_role):
        global main_window
        main_window = ModernMainWindow(username, user_role, login_window)
        main_window.showMaximized()


    login_window.login_successful.connect(on_login_success)
    login_window.show()
    sys.exit(app.exec())