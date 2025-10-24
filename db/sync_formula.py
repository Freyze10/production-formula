# sync_tool.py
# Standalone DBF to PostgreSQL Synchronization Tool for MBPI (v3 - Universal T_DELETED Skip)

import sys
import os
import traceback
import collections
from datetime import datetime

import sqlalchemy

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
PRODUCTION_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod01.dbf')
PRODUCTION_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod02.dbf')
RM_WH = os.path.join(DBF_BASE_PATH, 'tbl_rm_wh.dbf')

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
        self.setMinimumSize(400, 200)
        self.frame = QFrame(self)
        self.frame.setObjectName("HeaderCard")
        self.frame.setStyleSheet("""
            QFrame#HeaderCard { 
                background-color: #f8f9fa; 
                border-radius: 10px; 
                border: 1px solid #d0d0d0; 
            }
        """)
        main_layout = QVBoxLayout(self);
        main_layout.addWidget(self.frame)
        layout = QVBoxLayout(self.frame);
        layout.setContentsMargins(30, 30, 30, 30);
        layout.setSpacing(20)
        self.title_label = QLabel(title_text);
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold));
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #0078d4; font-family: 'Segoe UI';")
        self.animation_label = QLabel("Loading...");
        self.animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.animation_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.animation_label.setStyleSheet("color: #0078d4; font-family: 'Segoe UI';")
        self.progress_label = QLabel("Initializing...");
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
        self.progress_label.setWordWrap(True)
        self.progress_label.setFont(QFont("Segoe UI", 11))
        self.progress_label.setStyleSheet("color: #555; font-family: 'Segoe UI'; background-color: transparent; min-height:34px;")
        layout.addWidget(self.title_label);
        layout.addWidget(self.animation_label);
        layout.addWidget(self.progress_label)

    def update_progress(self, text):
        self.progress_label.setText(text)

    def closeEvent(self, event):
        event.accept()


# --- Synchronization Worker Classes ---
class SyncFormulaWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            with engine.connect() as conn:
                max_uid = conn.execute(text("SELECT COALESCE(MAX(uid), 0) FROM formula_primary")).scalar()
            self.progress.emit(f"Phase 1/3: Reading local formula items...")
            items_by_uid = collections.defaultdict(list)
            new_uids = set()
            dbf_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                ### CHANGE: Skip T_DELETED records ###
                if bool(item_rec.get('T_DELETED', False)):
                    continue
                uid = _to_int(item_rec.get('T_UID'))
                if uid is None or uid <= max_uid: continue
                new_uids.add(uid)
                items_by_uid[uid].append({
                    "uid": uid, "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "concentration": _to_float(item_rec.get('T_CON')),
                    "update_by": str(item_rec.get('T_UPDATEBY', '') or '').strip(),
                    "update_on_text": str(item_rec.get('T_UDATE', '') or '').strip()
                })
            self.progress.emit(f"Phase 1/3: Found {len(items_by_uid)} groups of new active items.")

            self.progress.emit("Phase 2/3: Reading Formula data...")
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                uid = _to_int(r.get('T_UID'))
                if uid is None or uid <= max_uid: continue
                primary_recs.append({
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(), "uid": uid,
                    "formula_date": r.get('T_DATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(), "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld": _to_float(r.get('T_LD')),
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

            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new valid records.")
            if not primary_recs: self.finished.emit(True,
                                                    f"Sync Info: No new formula records (UID > {max_uid}) found to sync."); return

            all_items_to_insert = [item for rec in primary_recs for item in items_by_uid.get(rec['uid'], [])]

            self.progress.emit("Phase 3/3: Syncing Data...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO formula_primary (
                            formula_index, uid, formula_date, customer, product_code, product_color, dosage, ld,
                            mix_type, resin, application, cm_num, cm_date, matched_by, encoded_by, remarks,
                            total_concentration, is_used, dbf_updated_by, dbf_updated_on_text, last_synced_on
                        )
                        VALUES (
                            :formula_index, :uid, :formula_date, :customer, :product_code, :product_color, :dosage, :ld,
                            :mix_type, :resin, :application, :cm_num, :cm_date, :matched_by, :encoded_by, :remarks,
                            :total_concentration, :is_used, :dbf_updated_by, :dbf_updated_on_text, NOW()
                        )
                        ON CONFLICT (uid) DO UPDATE SET
                            formula_index = EXCLUDED.formula_index,
                            formula_date = EXCLUDED.formula_date,
                            customer = EXCLUDED.customer,
                            product_code = EXCLUDED.product_code,
                            product_color = EXCLUDED.product_color,
                            dosage = EXCLUDED.dosage,
                            ld = EXCLUDED.ld,
                            mix_type = EXCLUDED.mix_type,
                            resin = EXCLUDED.resin,
                            application = EXCLUDED.application,
                            cm_num = EXCLUDED.cm_num,
                            cm_date = EXCLUDED.cm_date,
                            matched_by = EXCLUDED.matched_by,
                            encoded_by = EXCLUDED.encoded_by,
                            remarks = EXCLUDED.remarks,
                            total_concentration = EXCLUDED.total_concentration,
                            is_used = EXCLUDED.is_used,
                            dbf_updated_by = EXCLUDED.dbf_updated_by,
                            dbf_updated_on_text = EXCLUDED.dbf_updated_on_text,
                            last_synced_on = NOW();
                    """), primary_recs)
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO formula_items (uid, seq, material_code, concentration, update_by, update_on_text)
                            VALUES (:uid, :seq, :material_code, :concentration, :update_by, :update_on_text);
                        """), all_items_to_insert)
            self.finished.emit(True,
                               f"Formula sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required formula DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"FORMULA SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during formula sync:\n{e}")


class SyncProductionWorker(QObject):
    """
    Synchronizes production data from legacy DBF files (tbl_prod01, tbl_prod02)
    to PostgreSQL database tables (production_primary, production_items).

    Skips records where t_deleted = True.
    Excludes t_prodb and t_labb columns from tbl_prod02.
    """
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            # Get the maximum production ID already synced
            with engine.connect() as conn:
                max_prod_id = conn.execute(
                    text("SELECT COALESCE(MAX(prod_id), 0) FROM production_primary")
                ).scalar()

            self.progress.emit(f"Phase 1/3: Reading production items...")

            # Read production items from tbl_prod02.dbf
            items_by_prod_id = collections.defaultdict(list)
            new_prod_ids = set()

            dbf_items = dbfread.DBF(PRODUCTION_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')

            for item_rec in dbf_items:
                # Skip deleted records
                if bool(item_rec.get('T_DELETED', False)):
                    continue

                prod_id = _to_int(item_rec.get('T_PRODID'))
                if prod_id is None or prod_id <= max_prod_id:
                    continue

                new_prod_ids.add(prod_id)

                # Extract item data (excluding t_prodb and t_labb as requested)
                items_by_prod_id[prod_id].append({
                    "prod_id": prod_id,
                    "lot_num": str(item_rec.get('T_LOTNUM', '') or '').strip(),
                    "confirmation_date": item_rec.get('T_CDATE'),  # confirmation date
                    "production_date": item_rec.get('T_PRODDATE'),  # production date
                    "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "large_scale": _to_float(item_rec.get('T_PRODA')),  # Large scale (KG)
                    "small_scale": _to_float(item_rec.get('T_LABA')),  # Small scale (G)
                    # t_prodb and t_labb are intentionally excluded
                    "total_weight": _to_float(item_rec.get('T_WT')),  # Total weight
                    "total_loss": _to_float(item_rec.get('T_LOSS')),  # Total loss
                    "total_consumption": _to_float(item_rec.get('T_CONS'))  # Total consumption
                })

            self.progress.emit(f"Phase 1/3: Found {len(items_by_prod_id)} new active items.")

            # Read primary production data from tbl_prod01.dbf
            self.progress.emit("Phase 2/3: Reading Production data...")
            primary_recs = []

            dbf_primary = dbfread.DBF(PRODUCTION_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')

            for r in dbf_primary:
                # Skip deleted records
                if bool(r.get('T_DELETED', False)):
                    continue

                prod_id = _to_int(r.get('T_PRODID'))
                if prod_id is None or prod_id <= max_prod_id:
                    continue

                primary_recs.append({
                    "prod_id": prod_id,
                    "production_date": r.get('T_PRODDATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "formulation_id": _to_int(r.get('T_FID')),
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(),
                    "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld_percent": _to_float(r.get('T_LD')),
                    "lot_number": str(r.get('T_LOTNUM', '') or '').strip(),
                    "order_form_no": str(r.get('T_ORDERNUM', '') or '').strip(),
                    "colormatch_no": str(r.get('T_CMNUM', '') or '').strip(),
                    "colormatch_date": r.get('T_CMDATE'),
                    "mixing_time": str(r.get('T_MIXTIME', '') or '').strip(),
                    "machine_no": str(r.get('T_MACHINE', '') or '').strip(),
                    "qty_required": _to_float(r.get('T_QTYREQ')),
                    "qty_per_batch": _to_float(r.get('T_QTYBATCH')),
                    "qty_produced": _to_float(r.get('T_QTYPROD')),
                    "remarks": str(r.get('T_REMARKS', '') or '').strip(),
                    "notes": str(r.get('T_NOTE', '') or '').strip(),
                    "user_id": str(r.get('T_USERID', '') or '').strip(),
                    "prepared_by": str(r.get('T_PREPARED', '') or '').strip(),
                    "encoded_by": str(r.get('T_ENCODEDB', '') or '').strip(),
                    "encoded_on": r.get('T_ENCODEDO'),
                    "job_done": str(r.get('T_JDONE', '') or '').strip(),
                    "confirmation_date": r.get('T_CDATE'),
                    "scheduled_date": r.get('T_SDATE'),
                    "form_type": str(r.get('T_FTYPE', '') or '').strip()
                })

            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new records.")

            if not primary_recs:
                self.finished.emit(
                    True,
                    f"Sync Info: No new production records found to sync."
                )
                return

            # Collect all items to insert
            all_items_to_insert = [
                item
                for rec in primary_recs
                for item in items_by_prod_id.get(rec['prod_id'], [])
            ]

            # Write to database
            self.progress.emit("Phase 3/3: Syncing Data...")

            with engine.connect() as conn:
                with conn.begin():
                    # Insert/Update primary production records
                    conn.execute(text("""
                        INSERT INTO production_primary (
                            prod_id, production_date, customer, formulation_id, formula_index,
                            product_code, product_color, dosage, ld_percent, lot_number,
                            order_form_no, colormatch_no, colormatch_date, mixing_time, machine_no,
                            qty_required, qty_per_batch, qty_produced, remarks, notes,
                            user_id, prepared_by, encoded_by, encoded_on, job_done,
                            confirmation_date, scheduled_date, form_type, last_synced_on
                        )
                        VALUES (
                            :prod_id, :production_date, :customer, :formulation_id, :formula_index,
                            :product_code, :product_color, :dosage, :ld_percent, :lot_number,
                            :order_form_no, :colormatch_no, :colormatch_date, :mixing_time, :machine_no,
                            :qty_required, :qty_per_batch, :qty_produced, :remarks, :notes,
                            :user_id, :prepared_by, :encoded_by, :encoded_on, :job_done,
                            :confirmation_date, :scheduled_date, :form_type, NOW()
                        )
                        ON CONFLICT (prod_id) DO UPDATE SET
                            production_date = EXCLUDED.production_date,
                            customer = EXCLUDED.customer,
                            formulation_id = EXCLUDED.formulation_id,
                            formula_index = EXCLUDED.formula_index,
                            product_code = EXCLUDED.product_code,
                            product_color = EXCLUDED.product_color,
                            dosage = EXCLUDED.dosage,
                            ld_percent = EXCLUDED.ld_percent,
                            lot_number = EXCLUDED.lot_number,
                            order_form_no = EXCLUDED.order_form_no,
                            colormatch_no = EXCLUDED.colormatch_no,
                            colormatch_date = EXCLUDED.colormatch_date,
                            mixing_time = EXCLUDED.mixing_time,
                            machine_no = EXCLUDED.machine_no,
                            qty_required = EXCLUDED.qty_required,
                            qty_per_batch = EXCLUDED.qty_per_batch,
                            qty_produced = EXCLUDED.qty_produced,
                            remarks = EXCLUDED.remarks,
                            notes = EXCLUDED.notes,
                            user_id = EXCLUDED.user_id,
                            prepared_by = EXCLUDED.prepared_by,
                            encoded_by = EXCLUDED.encoded_by,
                            encoded_on = EXCLUDED.encoded_on,
                            job_done = EXCLUDED.job_done,
                            confirmation_date = EXCLUDED.confirmation_date,
                            scheduled_date = EXCLUDED.scheduled_date,
                            form_type = EXCLUDED.form_type,
                            last_synced_on = NOW();
                    """), primary_recs)

                    # Insert production items (materials)
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO production_items (
                                prod_id, lot_num, confirmation_date, production_date, seq,
                                material_code, large_scale, small_scale, total_weight,
                                total_loss, total_consumption
                            )
                            VALUES (
                                :prod_id, :lot_num, :confirmation_date, :production_date, :seq,
                                :material_code, :large_scale, :small_scale, :total_weight,
                                :total_loss, :total_consumption
                            );
                        """), all_items_to_insert)

            self.finished.emit(
                True,
                f"Production sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed."
            )

        except dbfread.DBFNotFound as e:
            self.finished.emit(
                False,
                f"File Not Found: A required production DBF file is missing.\nDetails: {e}"
            )
        except Exception as e:
            trace_info = traceback.format_exc()
            print(f"PRODUCTION SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(
                False,
                f"An unexpected error occurred during production sync:\n{e}"
            )

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
            with engine.connect() as conn:
                max_dr_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(dr_no AS INTEGER)), 0)
                    FROM product_delivery_primary
                    WHERE dr_no ~ '^[0-9]+$';
                """)).scalar()
            self.progress.emit(f"Phase 1/3: Reading delivery items from tbl_del02.dbf (filtering DR_NO > {max_dr_no})...")
            items_by_dr = {}
            dbf_items = dbfread.DBF(DELIVERY_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                ### CHANGE: Skip T_DELETED records ###
                if bool(item_rec.get('T_DELETED', False)):
                    continue
                dr_num = self._get_safe_dr_num(item_rec.get('T_DRNUM'))
                if not dr_num or int(dr_num) <= max_dr_no: continue
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
            self.progress.emit("Phase 2/3: Reading primary delivery data from tbl_del01.dbf...")
            primary_recs = []
            dbf_primary = dbfread.DBF(DELIVERY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                dr_num = self._get_safe_dr_num(r.get('T_DRNUM'))
                if not dr_num or int(dr_num) <= max_dr_no: continue
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
            if not primary_recs: self.finished.emit(True,
                                                    f"Sync Info: No new delivery records (DR_NO > {max_dr_no}) found to sync."); return
            all_items_to_insert = [item for dr_num in [rec['dr_no'] for rec in primary_recs] if dr_num in items_by_dr
                                   for item in items_by_dr[dr_num]]
            self.progress.emit("Phase 3/3: Writing delivery data to PostgreSQL database...")
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
                               f"Delivery sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed.")
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
            with engine.connect() as conn:
                max_rrf_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(rrf_no AS INTEGER)), 0)
                    FROM rrf_primary
                    WHERE rrf_no ~ '^[0-9]+$';
                """)).scalar()
            self.progress.emit(f"Reading RRF items (filtering RRF_NO > {max_rrf_no})...")
            items_by_rrf = {}
            dbf_items = dbfread.DBF(RRF_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                # Assuming RRF items don't have a T_DELETED flag as per structure
                rrf_num = self._get_safe_rrf_num(item_rec.get('T_DRNUM'));
                if not rrf_num or int(rrf_num) <= max_rrf_no: continue
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
            self.progress.emit("Reading primary RRF data...")
            primary_recs = []
            dbf_primary = dbfread.DBF(RRF_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                if bool(r.get('T_DELETED', False)):
                    continue
                rrf_num = self._get_safe_rrf_num(r.get('T_DRNUM'));
                if not rrf_num or int(rrf_num) <= max_rrf_no: continue
                primary_recs.append({
                    "rrf_no": rrf_num, "rrf_date": r.get('T_DRDATE'),
                    "customer_name": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "material_type": str(r.get('T_DELTO', '') or '').strip(),
                    "prepared_by": str(r.get('T_USERID', '') or '').strip()
                })
            if not primary_recs: self.finished.emit(True, f"Sync Info: No new RRF records (RRF_NO > {max_rrf_no}) found to sync."); return
            self.progress.emit("Writing RRF data to database...")
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
                               f"RRF sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required RRF DBF file is missing.\nDetails: {e}")
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred during RRF sync:\n{e}")


class SyncRMWarehouseWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("Phase 1/2: Reading warehouse data from tbl_rm_wh.dbf...")
            warehouse_recs = []
            dbf_warehouse = dbfread.DBF(RM_WH, encoding='latin1', char_decode_errors='ignore')

            for r in dbf_warehouse:
                if bool(r.get('T_DELETED', False)):
                    continue

                rm_code = str(r.get('T_MATCODE', '') or '').strip()
                if not rm_code:
                    continue

                warehouse_recs.append({
                    "rm_code": rm_code,
                    "ac": _to_float(r.get('T_AC', 0.0)),
                    "loss": _to_float(r.get('T_LOSS', 0.0))
                })

            self.progress.emit(f"Phase 1/2: Found {len(warehouse_recs)} valid records.")
            if not warehouse_recs:
                self.finished.emit(True, "Sync Info: No valid warehouse records found to sync.")
                return

            self.progress.emit("Phase 2/2: Writing warehouse data to database...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("TRUNCATE TABLE tbl_rm_warehouse RESTART IDENTITY"))
                    conn.execute(text("""
                        INSERT INTO tbl_rm_warehouse (rm_code, ac, loss, last_synced_on)
                        VALUES (:rm_code, :ac, :loss, NOW())
                    """), warehouse_recs)
            self.finished.emit(True,
                               f"RM Warehouse sync complete.\n{len(warehouse_recs)} records processed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

        except dbfread.DBFNotFound as e:
            error_msg = f"File Not Found: tbl_rm_wh.dbf is missing.\nDetails: {e}"
            print(error_msg)  # Debug: Log the error
            self.finished.emit(False, error_msg)
        except sqlalchemy.exc.SQLAlchemyError as e:
            error_msg = f"Database Error: Failed to execute SQL operation.\nDetails: {str(e)}"
            print(error_msg)  # Debug: Log the database error
            self.finished.emit(False, error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred during RM Warehouse sync:\n{str(e)}"
            print(error_msg)  # Debug: Log the unexpected error
            traceback.print_exc()  # Debug: Print full stack trace
            self.finished.emit(False, error_msg)


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
                        id SERIAL PRIMARY KEY,
                        formula_index VARCHAR(20) NOT NULL,
                        uid INTEGER NOT NULL UNIQUE,
                        formula_date DATE,
                        customer VARCHAR(100),
                        product_code VARCHAR(50),
                        product_color VARCHAR(50),
                        dosage NUMERIC(15,6),
                        ld NUMERIC(15,6),
                        mix_type VARCHAR(50),
                        resin VARCHAR(50),
                        application VARCHAR(100),
                        cm_num VARCHAR(20),
                        cm_date DATE,
                        matched_by VARCHAR(50),
                        encoded_by VARCHAR(50),
                        remarks TEXT,
                        total_concentration NUMERIC(15,6),
                        is_used BOOLEAN DEFAULT FALSE,
                        dbf_updated_by VARCHAR(100),
                        dbf_updated_on_text VARCHAR(100),
                        last_synced_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        mb_dc VARCHAR(5) DEFAULT 'MB',
                        html_code VARCHAR(10),
                        c INTEGER,
                        m INTEGER,
                        y INTEGER,
                        k INTEGER,
                        created_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT FALSE
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_primary_uid ON formula_primary (uid);"))
                connection.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_formula_primary_prod_code ON formula_primary (product_code);"))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS formula_items (
                        id SERIAL PRIMARY KEY, uid INTEGER NOT NULL, seq INTEGER, material_code VARCHAR(50), concentration NUMERIC(15, 6), update_by VARCHAR(100), update_on_text VARCHAR(100)
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_items_uid ON formula_items (uid);"))

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