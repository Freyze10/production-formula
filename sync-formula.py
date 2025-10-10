# sync_tool.py
# Standalone DBF to PostgreSQL Synchronization Tool for MBPI (v3 - Universal T_DELETED Skip, Incremental Sync)

import sys
import os
import traceback
import collections
from datetime import datetime

# --- Required Libraries ---
try:
    import dbfread
    from sqlalchemy import text, create_engine
    from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QSize
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGridLayout,
                                 QGroupBox, QPushButton, QLabel, QTextEdit, QMessageBox,
                                 QDialog, QFrame)
    from PyQt6.QtGui import QFont, QMovie
except ImportError as e:
    print(f"FATAL ERROR: A required library is missing: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
DB_CONFIG = {"host": "localhost", "port": 5433, "dbname": "db_formula", "user": "postgres", "password": "password"}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
DELIVERY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del01.dbf')
DELIVERY_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del02.dbf')
RRF_DBF_PATH = os.path.join(DBF_BASE_PATH, 'RRF')
RRF_PRIMARY_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del01.dbf')
RRF_ITEMS_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del02.dbf')
FORMULA_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula01.dbf')
FORMULA_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula02.dbf')

try:
    db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    print(f"CRITICAL: Could not create database engine. Error: {e}")


# --- Helper Functions ---
def _to_float(value, default=None):
    if value is None: return default
    if isinstance(value, bytes) and value.strip(b'\x00') == b'': return default
    try:
        return float(value)
    except (ValueError, TypeError):
        try:
            cleaned_value = str(value).strip().replace('\x00', '')
            return float(cleaned_value) if cleaned_value else default
        except (ValueError, TypeError):
            return default


def _to_int(value, default=None):
    if value is None: return default
    if isinstance(value, bytes) and value.strip(b'\x00') == b'': return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        try:
            cleaned_value = str(value).strip().replace('\x00', '')
            return int(float(cleaned_value)) if cleaned_value else default
        except (ValueError, TypeError):
            return default


# --- Loading Dialog Class ---
class LoadingDialog(QDialog):
    def __init__(self, title_text="Processing...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please Wait")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumSize(350, 150)
        self.frame = QFrame(self)
        self.frame.setStyleSheet(
            "QFrame { background-color: #ffffff; border-radius: 10px; border: 1px solid #d0d0d0; }")
        main_layout = QVBoxLayout(self);
        main_layout.addWidget(self.frame)
        layout = QVBoxLayout(self.frame);
        layout.setContentsMargins(20, 20, 20, 20);
        layout.setSpacing(15)
        self.title_label = QLabel(title_text);
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold));
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.animation_label = QLabel();
        self.animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gif_path = "loading.gif"
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path);
            self.movie.setScaledSize(QSize(40, 40));
            self.animation_label.setMovie(self.movie);
            self.movie.start()
        else:
            print("WARNING: 'loading.gif' not found. Displaying fallback text.")
            self.animation_label.setText("Loading...");
            self.animation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.progress_label = QLabel("Initializing...");
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.title_label);
        layout.addWidget(self.animation_label);
        layout.addWidget(self.progress_label)

    def update_progress(self, text):
        self.progress_label.setText(text)

    def closeEvent(self, event):
        if hasattr(self, 'movie'): self.movie.stop()
        event.accept()


# --- Synchronization Worker Classes ---
class SyncFormulaWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            # Get max legacy_id already synced
            with engine.connect() as conn:
                max_synced_legacy_id = conn.execute(text("""
                    SELECT COALESCE(MAX(legacy_id), 0)
                    FROM formula_primary
                    WHERE legacy_id IS NOT NULL;
                """)).scalar()
            self.progress.emit(f"Max synced legacy_id in PostgreSQL: {max_synced_legacy_id}")

            self.progress.emit("Phase 1/3: Reading formula items from tbl_formula02.dbf...")
            items_by_uid = collections.defaultdict(list)
            dbf_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                ### CHANGE: Skip T_DELETED records ###
                if bool(item_rec.get('T_DELETED', False)):
                    continue
                uid = _to_int(item_rec.get('T_UID'))
                if uid is None: continue
                items_by_uid[uid].append({
                    "uid": uid, "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "concentration": _to_float(item_rec.get('T_CON')),
                    "update_by": str(item_rec.get('T_UPDATEBY', '') or '').strip(),
                    "update_on_text": str(item_rec.get('T_UDATE', '') or '').strip()
                })
            self.progress.emit(f"Phase 1/3: Found items for {len(items_by_uid)} groups.")

            self.progress.emit("Phase 2/3: Reading primary formula data from tbl_formula01.dbf...")
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                legacy_id = _to_int(r.get('T_ID'))
                if legacy_id is None or legacy_id <= max_synced_legacy_id:
                    continue
                uid = _to_int(r.get('T_UID'))
                if uid is None: continue
                primary_recs.append({
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(), "uid": uid,
                    "formula_date": r.get('T_DATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(), "dosage": _to_float(r.get('T_DOSAGE')),
                    "legacy_id": legacy_id,
                    "mix_type": str(r.get('T_MIX', '') or '').strip(), "resin": str(r.get('T_RESIN', '') or '').strip(),
                    "application": str(r.get('T_APP', '') or '').strip(),
                    "cm_num": str(r.get('T_CMNUM', '') or '').strip(), "cm_date": r.get('T_CMDATE'),
                    "matched_by": str(r.get('T_MATCHBY', '') or '').strip(),
                    "encoded_by": str(r.get('T_ENCODEB', '') or '').strip(),
                    "remarks": str(r.get('T_REM', '') or '').strip(),
                    "total_concentration": _to_float(r.get('T_TOTALCON')), "is_used": bool(r.get('T_USED', False)),
                    "dbf_updated_by": str(r.get('T_UPDATEBY', '') or '').strip(),
                    "dbf_updated_on_text": str(r.get('T_UDATE', '') or '').strip(),
                })

            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new primary records (legacy_id > {max_synced_legacy_id}).")
            if not primary_recs:
                self.finished.emit(True, f"Sync Info: No new formula records (legacy_id > {max_synced_legacy_id}) found.")
                return

            self.progress.emit("Phase 3/3: Writing new data to PostgreSQL database...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO formula_primary (formula_index, uid, formula_date, customer, product_code, product_color, dosage, legacy_id, mix_type, resin, application, cm_num, cm_date, matched_by, encoded_by, remarks, total_concentration, is_used, dbf_updated_by, dbf_updated_on_text, last_synced_on)
                        VALUES (:formula_index, :uid, :formula_date, :customer, :product_code, :product_color, :dosage, :legacy_id, :mix_type, :resin, :application, :cm_num, :cm_date, :matched_by, :encoded_by, :remarks, :total_concentration, :is_used, :dbf_updated_by, :dbf_updated_on_text, NOW())
                        ON CONFLICT (formula_index) DO UPDATE SET
                            uid = EXCLUDED.uid, formula_date = EXCLUDED.formula_date, customer = EXCLUDED.customer, product_code = EXCLUDED.product_code, product_color = EXCLUDED.product_color, dosage = EXCLUDED.dosage, legacy_id = EXCLUDED.legacy_id,
                            mix_type = EXCLUDED.mix_type, resin = EXCLUDED.resin, application = EXCLUDED.application, cm_num = EXCLUDED.cm_num, cm_date = EXCLUDED.cm_date, matched_by = EXCLUDED.matched_by, encoded_by = EXCLUDED.encoded_by,
                            remarks = EXCLUDED.remarks, total_concentration = EXCLUDED.total_concentration, is_used = EXCLUDED.is_used, dbf_updated_by = EXCLUDED.dbf_updated_by, dbf_updated_on_text = EXCLUDED.dbf_updated_on_text, last_synced_on = NOW();
                    """), primary_recs)
                    all_items_to_insert = [item for rec in primary_recs for item in items_by_uid.get(rec['uid'], [])]
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO formula_items (uid, seq, material_code, concentration, update_by, update_on_text)
                            VALUES (:uid, :seq, :material_code, :concentration, :update_by, :update_on_text);
                        """), all_items_to_insert)
            self.finished.emit(True,
                               f"Formula sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} new items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required formula DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"FORMULA SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during formula sync:\n{e}")


class SyncDeliveryWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def _get_safe_dr_num(self, dr_num_raw):
        if dr_num_raw is None: return None
        try:
            return str(int(float(dr_num_raw)))
        except (ValueError, TypeError):
            return str(dr_num_raw).strip() if dr_num_raw else None

    def run(self):
        try:
            # Get max dr_no already synced
            with engine.connect() as conn:
                max_synced_dr_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(dr_no AS INTEGER)), 0)
                    FROM product_delivery_primary
                    WHERE dr_no ~ '^[0-9]+$';
                """)).scalar()
            self.progress.emit(f"Max synced DR_NO in PostgreSQL: {max_synced_dr_no}")

            self.progress.emit("Phase 1/3: Reading delivery items from tbl_del02.dbf...")
            items_by_dr = {}
            dbf_items = dbfread.DBF(DELIVERY_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                ### CHANGE: Skip T_DELETED records ###
                if bool(item_rec.get('T_DELETED', False)):
                    continue
                dr_num = self._get_safe_dr_num(item_rec.get('T_DRNUM'))
                if not dr_num: continue
                if dr_num not in items_by_dr: items_by_dr[dr_num] = []
                attachments = "\n".join(
                    filter(None, [str(item_rec.get(f'T_DESC{i}', '') or '').strip() for i in range(1, 5)]))
                items_by_dr[dr_num].append({
                    "dr_no": dr_num, "quantity": _to_float(item_rec.get('T_TOTALWT')),
                    "unit": str(item_rec.get('T_TOTALWTU', '') or '').strip(),
                    "product_code": str(item_rec.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(item_rec.get('T_PRODCOLO', '') or '').strip(),
                    "no_of_packing": _to_float(item_rec.get('T_NUMPACKI')),
                    "weight_per_pack": _to_float(item_rec.get('T_WTPERPAC')),
                    "lot_numbers": "", "attachments": attachments, "unit_price": None, "lot_no_1": None,
                    "lot_no_2": None, "lot_no_3": None, "mfg_date": None, "alias_code": None, "alias_desc": None
                })
            self.progress.emit(f"Phase 1/3: Found items for {len(items_by_dr)} DRs.")

            self.progress.emit("Phase 2/3: Reading primary delivery data from tbl_del01.dbf...")
            primary_recs = []
            dbf_primary = dbfread.DBF(DELIVERY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                dr_num_raw = r.get('T_DRNUM')
                dr_num = self._get_safe_dr_num(dr_num_raw)
                if not dr_num or not dr_num.isdigit():
                    continue
                dr_num_int = int(dr_num)
                if dr_num_int <= max_synced_dr_no:
                    continue
                address = (str(r.get('T_ADD1', '') or '').strip() + ' ' + str(
                    r.get('T_ADD2', '') or '').strip()).strip()
                primary_recs.append({
                    "dr_no": dr_num, "delivery_date": r.get('T_DRDATE'),
                    "customer_name": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "deliver_to": str(r.get('T_DELTO', '') or '').strip(), "address": address,
                    "po_no": str(r.get('T_CPONUM', '') or '').strip(),
                    "order_form_no": str(r.get('T_ORDERNUM', '') or '').strip(),
                    "terms": str(r.get('T_REMARKS', '') or '').strip(),
                    "prepared_by": str(r.get('T_USERID', '') or '').strip(), "encoded_on": r.get('T_DENCODED')
                })
            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new primary records (DR_NO > {max_synced_dr_no}).")
            if not primary_recs:
                self.finished.emit(True, f"Sync Info: No new delivery records (DR_NO > {max_synced_dr_no}) found.")
                return
            all_items_to_insert = [item for dr_num in [rec['dr_no'] for rec in primary_recs] if dr_num in items_by_dr
                                   for item in items_by_dr[dr_num]]
            self.progress.emit("Phase 3/3: Writing new delivery data to PostgreSQL database...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO product_delivery_primary (dr_no, delivery_date, customer_name, deliver_to, address, po_no, order_form_no, terms, prepared_by, encoded_on, edited_by, edited_on, encoded_by)
                        VALUES (:dr_no, :delivery_date, :customer_name, :deliver_to, :address, :po_no, :order_form_no, :terms, :prepared_by, :encoded_on, 'DBF_SYNC', NOW(), :prepared_by)
                        ON CONFLICT (dr_no) DO UPDATE SET
                            delivery_date = EXCLUDED.delivery_date, customer_name = EXCLUDED.customer_name, deliver_to = EXCLUDED.deliver_to, address = EXCLUDED.address, po_no = EXCLUDED.po_no,
                            order_form_no = EXCLUDED.order_form_no, terms = EXCLUDED.terms, prepared_by = EXCLUDED.prepared_by, encoded_on = EXCLUDED.encoded_on, edited_by = 'DBF_SYNC', edited_on = NOW()
                    """), primary_recs)
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO product_delivery_items (dr_no, quantity, unit, product_code, product_color, no_of_packing, weight_per_pack, lot_numbers, attachments, unit_price, lot_no_1, lot_no_2, lot_no_3, mfg_date, alias_code, alias_desc)
                            VALUES (:dr_no, :quantity, :unit, :product_code, :product_color, :no_of_packing, :weight_per_pack, :lot_numbers, :attachments, :unit_price, :lot_no_1, :lot_no_2, :lot_no_3, :mfg_date, :alias_code, :alias_desc)
                        """), all_items_to_insert)
            self.finished.emit(True,
                               f"Delivery sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} new items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required delivery DBF file is missing.\nDetails: {e}")
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred during delivery sync:\n{e}")


class SyncRRFWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def _get_safe_rrf_num(self, rrf_num_raw):
        if rrf_num_raw is None: return None
        try:
            return str(int(float(rrf_num_raw)))
        except (ValueError, TypeError):
            return str(rrf_num_raw).strip() if rrf_num_raw else None

    def run(self):
        try:
            # Get max rrf_no already synced
            with engine.connect() as conn:
                max_synced_rrf_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(rrf_no AS INTEGER)), 0)
                    FROM rrf_primary
                    WHERE rrf_no ~ '^[0-9]+$';
                """)).scalar()
            self.progress.emit(f"Max synced RRF_NO in PostgreSQL: {max_synced_rrf_no}")

            self.progress.emit("Phase 1/3: Reading RRF items from tbl_del02.dbf...")
            items_by_rrf = {}
            dbf_items = dbfread.DBF(RRF_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                # Assuming RRF items don't have a T_DELETED flag as per structure
                rrf_num = self._get_safe_rrf_num(item_rec.get('T_DRNUM'));
                if not rrf_num: continue
                if rrf_num not in items_by_rrf: items_by_rrf[rrf_num] = []
                remarks = "\n".join(
                    filter(None, [str(item_rec.get(f'T_DESC{i}', '') or '').strip() for i in range(3, 5)]))
                items_by_rrf[rrf_num].append({
                    "rrf_no": rrf_num, "quantity": _to_float(item_rec.get('T_TOTALWT')),
                    "unit": str(item_rec.get('T_TOTALWTU', '') or '').strip(),
                    "product_code": str(item_rec.get('T_PRODCODE', '') or '').strip(),
                    "lot_number": str(item_rec.get('T_DESC1', '') or '').strip(),
                    "reference_number": str(item_rec.get('T_DESC2', '') or '').strip(), "remarks": remarks
                })
            self.progress.emit(f"Phase 1/3: Found items for {len(items_by_rrf)} RRFs.")

            self.progress.emit("Phase 2/3: Reading primary RRF data from tbl_del01.dbf...")
            primary_recs = []
            dbf_primary = dbfread.DBF(RRF_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                rrf_num_raw = r.get('T_DRNUM')
                rrf_num = self._get_safe_rrf_num(rrf_num_raw)
                if not rrf_num or not rrf_num.isdigit():
                    continue
                rrf_num_int = int(rrf_num)
                if rrf_num_int <= max_synced_rrf_no:
                    continue
                primary_recs.append({
                    "rrf_no": rrf_num, "rrf_date": r.get('T_DRDATE'),
                    "customer_name": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "material_type": str(r.get('T_DELTO', '') or '').strip(),
                    "prepared_by": str(r.get('T_USERID', '') or '').strip()
                })
            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new primary records (RRF_NO > {max_synced_rrf_no}).")
            if not primary_recs:
                self.finished.emit(True, f"Sync Info: No new RRF records (RRF_NO > {max_synced_rrf_no}) found.")
                return
            self.progress.emit("Phase 3/3: Writing new RRF data to database...")
            with engine.connect() as conn:
                with conn.begin():
                    ### CHANGE: Simplified SQL to remove is_deleted ###
                    conn.execute(text("""
                        INSERT INTO rrf_primary (rrf_no, rrf_date, customer_name, material_type, prepared_by, encoded_by, encoded_on, edited_by, edited_on)
                        VALUES (:rrf_no, :rrf_date, :customer_name, :material_type, :prepared_by, 'DBF_SYNC', NOW(), 'DBF_SYNC', NOW())
                        ON CONFLICT (rrf_no) DO UPDATE SET 
                            rrf_date = EXCLUDED.rrf_date, customer_name = EXCLUDED.customer_name, material_type = EXCLUDED.material_type, 
                            prepared_by = EXCLUDED.prepared_by, edited_by = 'DBF_SYNC', edited_on = NOW()
                    """), primary_recs)
                    all_items_to_insert = [item for rrf_num in [rec['rrf_no'] for rec in primary_recs] if rrf_num in items_by_rrf for item
                                           in items_by_rrf[rrf_num]]
                    if all_items_to_insert:
                        conn.execute(text(
                            """INSERT INTO rrf_items (rrf_no, quantity, unit, product_code, lot_number, reference_number, remarks) VALUES (:rrf_no, :quantity, :unit, :product_code, :lot_number, :reference_number, :remarks)"""),
                                     all_items_to_insert)
            self.finished.emit(True,
                               f"RRF sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} new items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required RRF DBF file is missing.\nDetails: {e}")
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred during RRF sync:\n{e}")


# --- Main Application Window ---
class SyncToolWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.threads = {}
        self.loading_dialog = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MBPI Legacy Data Synchronization Tool")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI'; font-size: 10pt; }
            QGroupBox { font-weight: bold; }
            QPushButton { padding: 8px; border-radius: 4px; border: 1px solid #ccc; background-color: #f0f0f0; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:disabled { background-color: #d3d3d3; color: #888; }
            QTextEdit { font-family: 'Consolas', 'Courier New', monospace; background-color: #fdfdfd; }
            QLabel#status_success { color: green; font-weight: bold; }
            QLabel#status_error { color: red; font-weight: bold; }
        """)
        main_layout = QVBoxLayout(self)
        title = QLabel("MBPI DBF Synchronization Utility")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        grid_layout = QGridLayout()
        self.formula_group, self.formula_btn, self.formula_status = self.create_sync_group("Formula Sync",
                                                                                           self.start_formula_sync)
        grid_layout.addWidget(self.formula_group, 0, 0)
        self.delivery_group, self.delivery_btn, self.delivery_status = self.create_sync_group("Product Delivery Sync",
                                                                                              self.start_delivery_sync)
        grid_layout.addWidget(self.delivery_group, 0, 1)
        self.rrf_group, self.rrf_btn, self.rrf_status = self.create_sync_group("RRF Sync", self.start_rrf_sync)
        grid_layout.addWidget(self.rrf_group, 0, 2)
        main_layout.addLayout(grid_layout)
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_layout.addWidget(self.log_widget)
        main_layout.addWidget(log_group)

    def create_sync_group(self, title, on_click_handler):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        button = QPushButton(f"Start {title}")
        button.clicked.connect(on_click_handler)
        status_label = QLabel("Status: Ready")
        layout.addWidget(button)
        layout.addWidget(status_label)
        return group, button, status_label

    def log_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_widget.append(f"[{timestamp}] {message}")

    def start_sync_task(self, task_name, worker_class, button, status_label, dialog_title):
        if task_name in self.threads and self.threads[task_name].isRunning():
            self.log_message(f"Warning: {task_name} sync is already running.")
            return

        button.setEnabled(False)
        status_label.setText("Status: Running...")
        status_label.setObjectName("")
        status_label.setStyleSheet(self.styleSheet())
        self.log_message(f"Starting {task_name} sync...")

        self.loading_dialog = LoadingDialog(dialog_title, self)
        thread = QThread()
        worker = worker_class()
        worker.moveToThread(thread)
        worker.progress.connect(self.loading_dialog.update_progress)
        worker.finished.connect(lambda s, m: self.on_sync_finished(task_name, s, m, button, status_label, thread))
        thread.started.connect(worker.run)
        thread.start()
        self.threads[task_name] = thread
        self.loading_dialog.exec()

    def on_sync_finished(self, task_name, success, message, button, status_label, thread):
        if self.loading_dialog and self.loading_dialog.isVisible():
            self.loading_dialog.accept()
        self.loading_dialog = None

        self.log_message(f"--- {task_name} Sync Finished ---")
        self.log_message(message)

        if success:
            status_label.setText(f"Status: Success ({datetime.now().strftime('%H:%M')})")
            status_label.setObjectName("status_success")
            QMessageBox.information(self, f"{task_name} Sync Result", message)
        else:
            status_label.setText(f"Status: FAILED ({datetime.now().strftime('%H:%M')})")
            status_label.setObjectName("status_error")
            QMessageBox.critical(self, f"{task_name} Sync Error", message)

        status_label.setStyleSheet(self.styleSheet())
        button.setEnabled(True)

        thread.quit()
        thread.wait()
        if task_name in self.threads:
            del self.threads[task_name]

    def start_formula_sync(self):
        self.start_sync_task("Formula", SyncFormulaWorker, self.formula_btn, self.formula_status,
                             dialog_title="Syncing Formula Data")

    def start_delivery_sync(self):
        self.start_sync_task("Delivery", SyncDeliveryWorker, self.delivery_btn, self.delivery_status,
                             dialog_title="Syncing Delivery Records")

    def start_rrf_sync(self):
        self.start_sync_task("RRF", SyncRRFWorker, self.rrf_btn, self.rrf_status, dialog_title="Syncing RRF Records")

    def closeEvent(self, event):
        running_threads = [t for t in self.threads.values() if t.isRunning()]
        if running_threads:
            reply = QMessageBox.question(self, 'Confirm Exit',
                                         "A sync process is still running. Are you sure you want to exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for thread in running_threads: thread.quit(); thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# --- Database Initialization ---
def initialize_sync_tool_db():
    print("Checking database schema for sync tool...")
    try:
        with engine.connect() as connection:
            with connection.begin():
                # Schema for formula tables
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS formula_primary (
                        id SERIAL PRIMARY KEY, formula_index VARCHAR(20) UNIQUE NOT NULL, uid INTEGER, formula_date DATE, customer VARCHAR(100), product_code VARCHAR(50), product_color VARCHAR(50), dosage NUMERIC(15, 6),
                        legacy_id INTEGER, mix_type VARCHAR(50), resin VARCHAR(50), application VARCHAR(100), cm_num VARCHAR(20), cm_date DATE, matched_by VARCHAR(50), encoded_by VARCHAR(50), remarks TEXT,
                        total_concentration NUMERIC(15, 6), is_used BOOLEAN, dbf_updated_by VARCHAR(100), dbf_updated_on_text VARCHAR(100), last_synced_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_primary_uid ON formula_primary (uid);"))
                connection.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_formula_primary_prod_code ON formula_primary (product_code);"))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS formula_items (
                        id SERIAL PRIMARY KEY, uid INTEGER NOT NULL, seq INTEGER, material_code VARCHAR(50), concentration NUMERIC(15, 6), update_by VARCHAR(100), update_on_text VARCHAR(100)
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_items_uid ON formula_items (uid);"))

                # Schema for delivery tables (assuming they exist or create if needed)
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_primary (
                        id SERIAL PRIMARY KEY, dr_no TEXT NOT NULL UNIQUE, delivery_date DATE, customer_name TEXT,
                        deliver_to TEXT, address TEXT, po_no TEXT, order_form_no TEXT, terms TEXT,
                        prepared_by TEXT, encoded_by TEXT, encoded_on TIMESTAMP, edited_by TEXT, edited_on TIMESTAMP
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_delivery_primary_dr_no ON product_delivery_primary (dr_no);"))

                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_items (
                        id SERIAL PRIMARY KEY, dr_no TEXT NOT NULL, quantity NUMERIC(15, 6), unit TEXT,
                        product_code TEXT, product_color TEXT, no_of_packing NUMERIC(15, 2), weight_per_pack NUMERIC(15, 6),
                        lot_numbers TEXT, attachments TEXT, unit_price NUMERIC(15, 6), lot_no_1 TEXT, lot_no_2 TEXT,
                        lot_no_3 TEXT, mfg_date TEXT, alias_code TEXT, alias_desc TEXT,
                        FOREIGN KEY (dr_no) REFERENCES product_delivery_primary (dr_no) ON DELETE CASCADE
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_delivery_items_dr_no ON product_delivery_items (dr_no);"))

                # Schema for RRF tables (ensure is_deleted column is NOT there)
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_primary (
                        id SERIAL PRIMARY KEY, rrf_no TEXT NOT NULL UNIQUE, rrf_date DATE, customer_name TEXT,
                        material_type TEXT, prepared_by TEXT, encoded_by TEXT, encoded_on TIMESTAMP,
                        edited_by TEXT, edited_on TIMESTAMP
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_rrf_primary_rrf_no ON rrf_primary (rrf_no);"))
                connection.execute(text("ALTER TABLE rrf_primary DROP COLUMN IF EXISTS is_deleted;"))

                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_items (
                        id SERIAL PRIMARY KEY, rrf_no TEXT NOT NULL, quantity NUMERIC(15, 6), unit TEXT,
                        product_code TEXT, lot_number TEXT, reference_number TEXT, remarks TEXT,
                        FOREIGN KEY (rrf_no) REFERENCES rrf_primary (rrf_no) ON DELETE CASCADE
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_rrf_items_rrf_no ON rrf_items (rrf_no);"))

        print("Database schema check complete.")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR during database initialization: {e}")
        return False


# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not initialize_sync_tool_db():
        QMessageBox.critical(None, "Database Error",
                             "Could not connect to or initialize the database.\nCheck console for details.")
        sys.exit(1)
    main_window = SyncToolWindow()
    main_window.show()
    sys.exit(app.exec())