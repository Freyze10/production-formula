# database/schema.py
from sqlalchemy import text


def initialize_database(engine):
    """Initializes the database schema and default data."""
    print("Initializing database schema...")
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                # Users table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        username TEXT UNIQUE NOT NULL, 
                        password TEXT NOT NULL, 
                        qc_access BOOLEAN DEFAULT TRUE, 
                        role TEXT DEFAULT 'Editor'
                    );
                """))

                # Audit trail table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS qc_audit_trail (
                        id SERIAL PRIMARY KEY, 
                        timestamp TIMESTAMP, 
                        username TEXT, 
                        action_type TEXT, 
                        details TEXT, 
                        hostname TEXT, 
                        ip_address TEXT, 
                        mac_address TEXT
                    );
                """))

                # Formula primary table
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
                    );
                """))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_primary_uid ON formula_primary (uid);"))
                connection.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_formula_primary_prod_code ON formula_primary (product_code);"))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS formula_items (
                        id SERIAL PRIMARY KEY, uid INTEGER NOT NULL, seq INTEGER, material_code VARCHAR(50), concentration NUMERIC(15, 6), update_by VARCHAR(100), update_on_text VARCHAR(100)
                    );
                """))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_formula_items_uid ON formula_items (uid);"))
                # Schema for RM Warehouse table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS tbl_rm_warehouse (
                        id SERIAL PRIMARY KEY,
                        rm_code VARCHAR(50) UNIQUE NOT NULL,
                        ac NUMERIC(15, 6),
                        loss NUMERIC(15, 6),
                        last_synced_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                connection.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_rm_warehouse_rm_code ON tbl_rm_warehouse (rm_code);"))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS production_primary (
                        prod_id INTEGER PRIMARY KEY,
                        production_date DATE,
                        customer VARCHAR(100),
                        formulation_id INTEGER,
                        formula_index VARCHAR(20),
                        product_code VARCHAR(30),
                        product_color VARCHAR(50),
                        dosage NUMERIC(10, 5),
                        ld_percent NUMERIC(10, 5),
                        lot_number VARCHAR(30),
                        order_form_no VARCHAR(50),
                        colormatch_no VARCHAR(30),
                        colormatch_date DATE,
                        mixing_time VARCHAR(20),
                        machine_no VARCHAR(30),
                        qty_required NUMERIC(15, 7),
                        qty_per_batch NUMERIC(15, 7),
                        qty_produced NUMERIC(15, 7),
                        remarks VARCHAR(100),
                        notes TEXT,
                        user_id VARCHAR(50),
                        prepared_by VARCHAR(50),
                        encoded_by VARCHAR(50),
                        encoded_on TIMESTAMP,
                        job_done VARCHAR(20),
                        confirmation_date DATE,
                        scheduled_date TIMESTAMP,
                        form_type VARCHAR(100),
                        last_synced_on TIMESTAMP DEFAULT NOW(),
                        is_manual BOOLEAN DEFAULT False
                    );"""))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS production_items (
                        id SERIAL PRIMARY KEY,
                        prod_id INTEGER REFERENCES production_primary(prod_id) ON DELETE CASCADE,
                        lot_num VARCHAR(30),
                        confirmation_date DATE,
                        production_date DATE,
                        seq INTEGER,
                        material_code VARCHAR(30),
                        large_scale NUMERIC(15, 6),
                        small_scale NUMERIC(15, 6),
                        total_weight NUMERIC(15, 7),
                        total_loss NUMERIC(15, 6),
                        total_consumption NUMERIC(15, 6)
                    );"""))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_production_primary_date ON production_primary(production_date);"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_production_primary_customer ON production_primary(customer);"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_production_primary_lot ON production_primary(lot_number);"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_production_items_prod_id ON production_items(prod_id);"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_production_items_material ON production_items(material_code);"))

                # Insert default users
                default_users = [
                    {"user": "admin", "pwd": "itadmin", "role": "Admin"},
                    {"user": "itsup", "pwd": "itsup", "role": "Editor"}
                ]
                user_insert_query = text(
                    "INSERT INTO users (username, password, role) VALUES (:user, :pwd, :role) ON CONFLICT (username) DO NOTHING;"
                )
                connection.execute(user_insert_query, default_users)

                transaction.commit()
        print("Database initialized successfully.")
        return True

    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False


def get_user_credentials(engine, username):
    """Retrieves user credentials and role from database."""
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT password, qc_access, role FROM users WHERE username=:u"),
                {"u": username}
            ).fetchone()
            return result
    except Exception as e:
        print(f"Error retrieving user credentials: {e}")
        return None


def log_audit_trail(engine, username, action_type, details, workstation_info):
    """Logs an entry to the audit trail."""
    try:
        log_query = text("""
            INSERT INTO qc_audit_trail (
                timestamp, username, action_type, details, 
                hostname, ip_address, mac_address
            ) VALUES (
                NOW(), :u, :a, :d, :h, :i, :m
            )
        """)
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(
                    log_query,
                    {
                        "u": username,
                        "a": action_type,
                        "d": details,
                        **workstation_info
                    }
                )
        return True
    except Exception as e:
        print(f"Audit trail logging failed: {e}")
        return False


def test_database_connection(engine):
    """Tests the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False