# database/engine_conn.py - Enhanced version
import os
import dbfread
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from PyQt6.QtCore import pyqtSignal, QObject

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "db_formula",
    "user": "postgres",
    "password": "password"
}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
PRODUCTION_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod01.dbf')


def get_database_url():
    """Returns the database connection URL."""
    return f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"


def create_engine_connection():
    """Creates and returns a SQLAlchemy engine."""
    db_url = get_database_url()
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
    return engine


class SyncWorker(QObject):
    """Worker class for syncing legacy production data."""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)  # Optional progress updates

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        logger.info("SyncWorker initialized")

    def run(self):
        """Executes the sync process in background."""
        logger.info(f"🚀 Legacy sync started - Target: {PRODUCTION_DBF_PATH}")
        self.progress.emit("Connecting to legacy DBF file...")

        try:
            # Check DBF accessibility
            if not os.path.exists(PRODUCTION_DBF_PATH):
                error_msg = f"DBF file not accessible: {PRODUCTION_DBF_PATH}"
                logger.error(error_msg)
                self.finished.emit(False, error_msg)
                return

            logger.info(f"✅ DBF file found: {PRODUCTION_DBF_PATH}")
            self.progress.emit("Reading DBF records...")

            # Read DBF file
            dbf = dbfread.DBF(PRODUCTION_DBF_PATH, load=True, encoding='latin1')

            if 'T_LOTNUM' not in dbf.field_names:
                error_msg = "Sync Error: Required column 'T_LOTNUM' not found in DBF."
                logger.error(error_msg)
                self.finished.emit(False, error_msg)
                return

            # Process records with progress
            recs = []
            total_records = len(list(dbf.records))  # Get total count
            dbf = dbfread.DBF(PRODUCTION_DBF_PATH, load=True, encoding='latin1')  # Reopen

            logger.info(f"📊 Processing {total_records} records from DBF")
            valid_count = 0

            for i, r in enumerate(dbf.records, 1):
                lot_num = str(r.get('T_LOTNUM', '')).strip()
                if not lot_num:
                    continue

                rec = {
                    "lot": lot_num.upper(),
                    "code": str(r.get('T_PRODCODE', '')).strip(),
                    "cust": str(r.get('T_CUSTOMER', '')).strip(),
                    "fid": str(int(r.get('T_FID'))) if r.get('T_FID') is not None else '',
                    "op": str(r.get('T_OPER', '')).strip(),
                    "sup": str(r.get('T_SUPER', '')).strip()
                }
                recs.append(rec)
                valid_count += 1

                # Periodic progress update
                if i % 100 == 0:
                    self.progress.emit(f"Processed {i}/{total_records} records...")

            logger.info(f"✅ Valid records to sync: {valid_count}")

            if not recs:
                msg = "No valid records found in DBF file to sync."
                logger.info(msg)
                self.finished.emit(True, msg)
                return

            self.progress.emit("Syncing to database...")

            # Batch sync to database
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(text("""
                        INSERT INTO legacy_production(
                            lot_number, prod_code, customer_name, formula_id, 
                            operator, supervisor, last_synced_on
                        ) VALUES(
                            :lot, :code, :cust, :fid, :op, :sup, NOW()
                        ) ON CONFLICT(lot_number) DO UPDATE SET 
                            prod_code=EXCLUDED.prod_code, 
                            customer_name=EXCLUDED.customer_name, 
                            formula_id=EXCLUDED.formula_id, 
                            operator=EXCLUDED.operator, 
                            supervisor=EXCLUDED.supervisor, 
                            last_synced_on=NOW()
                    """), recs)

                    updated_rows = result.rowcount
                    logger.info(f"✅ Database sync completed: {updated_rows} rows affected")

            success_msg = f"Legacy sync complete: {len(recs)} records processed, {updated_rows} updated/inserted."
            logger.info(success_msg)
            self.finished.emit(True, success_msg)

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.finished.emit(False, error_msg)