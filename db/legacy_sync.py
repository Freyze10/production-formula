# database/legacy_sync.py
import os
import dbfread
from datetime import datetime
from sqlalchemy import create_engine, text
from PyQt6.QtCore import pyqtSignal, QObject

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
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)


class SyncWorker(QObject):
    """Worker class for syncing legacy production data."""
    finished = pyqtSignal(bool, str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        """Executes the sync process."""
        try:
            # Validate DBF file exists
            if not os.path.exists(PRODUCTION_DBF_PATH):
                self.finished.emit(False, f"File Not Found: Production DBF not found at:\n{PRODUCTION_DBF_PATH}")
                return

            # Read DBF file
            dbf = dbfread.DBF(PRODUCTION_DBF_PATH, load=True, encoding='latin1')

            # Validate required fields
            if 'T_LOTNUM' not in dbf.field_names:
                self.finished.emit(False, "Sync Error: Required column 'T_LOTNUM' not found.")
                return

            # Process records
            recs = []
            for r in dbf.records:
                lot_num = str(r.get('T_LOTNUM', '')).strip()
                if not lot_num:  # Skip empty lot numbers
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

            if not recs:
                self.finished.emit(True, "Sync Info: No new records found in DBF file to sync.")
                return

            # Sync to database
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
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

            self.finished.emit(True, f"Production sync complete.\n{len(recs)} records processed.")

        except dbfread.DBFNotFound:
            self.finished.emit(False, f"File Not Found: Production DBF not found at:\n{PRODUCTION_DBF_PATH}")
        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred during sync:\n{str(e)}")