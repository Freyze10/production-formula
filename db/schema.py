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

                # Legacy production table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS legacy_production (
                        lot_number TEXT PRIMARY KEY, 
                        prod_code TEXT, 
                        customer_name TEXT, 
                        formula_id TEXT, 
                        operator TEXT, 
                        supervisor TEXT, 
                        last_synced_on TIMESTAMP
                    );
                """))

                # Index for legacy production
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_legacy_production_lot_number 
                    ON legacy_production (lot_number);
                """))

                # Formula primary table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS formula_primary (
                        id SERIAL PRIMARY KEY,
                        formula_index VARCHAR(20) NOT NULL UNIQUE,
                        uid INTEGER,
                        formula_date DATE,
                        customer VARCHAR(100),
                        product_code VARCHAR(50),
                        product_color VARCHAR(50),
                        dosage NUMERIC(15,6),
                        legacy_id INTEGER,
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