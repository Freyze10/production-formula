import psycopg2


def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="db_formula",
        user="postgres",
        password="password",
        port="5433"
    )


def get_formula_data(early_date, late_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT uid, formula_index, formula_date, customer, product_code, product_color, total_concentration, dosage
        FROM formula_primary
        WHERE formula_date BETWEEN %s AND %s
        ORDER BY uid DESC
    """, (early_date, late_date))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


def get_formula_materials(uid):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT material_code, concentration FROM formula_items WHERE uid = %s ORDER BY seq DESC",
                (uid,))
    records = cur.fetchall()

    cur.close()
    conn.close()
    return records


def get_specific_formula_data(uid):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM formula_primary WHERE uid = %s",
                (uid,))
    records = cur.fetchone()

    cur.close()
    conn.close()
    return records


def get_min_max_formula_date():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT MIN(formula_date) AS earliest_date,
                            MAX(formula_date) AS latest_date
                    FROM formula_primary""")
    record = cur.fetchone()

    cur.close()
    conn.close()
    return record


def get_formula_latest_uid():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT MAX(uid)
                    FROM formula_primary""")
    record = cur.fetchone()

    cur.close()
    conn.close()
    return record


def save_formula(primary_data, material_composition):
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Insert into formula_primary - using all fields from primary_data
        cur.execute("""
            INSERT INTO formula_primary (
                uid, formula_index, customer, product_code, product_color, 
                total_concentration, dosage, mix_type, resin, application, 
                cm_num, cm_date, remarks, mb_dc, html_code, c, m, y, k, 
                matched_by, encoded_by, formula_date, dbf_updated_by, dbf_updated_on_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING uid;
        """, (
            primary_data["uid"],
            primary_data["formula_index"],
            primary_data["customer"],
            primary_data["product_code"],
            primary_data["product_color"],
            primary_data["total_concentration"],
            primary_data["dosage"],
            primary_data["mix_type"],
            primary_data["resin"],
            primary_data["application"],
            primary_data["cm_num"],
            primary_data["cm_date"],
            primary_data["remarks"],
            primary_data["mb_dc"],
            primary_data["html_code"],
            primary_data["c"],
            primary_data["m"],
            primary_data["y"],
            primary_data["k"],
            primary_data["matched_by"],
            primary_data["encoded_by"],
            primary_data["formula_date"],
            primary_data["dbf_updated_by"],
            primary_data["dbf_updated_on_text"]
        ))

        uid = cur.fetchone()[0]

        # Insert material composition - preserve row order with sequence number
        for idx, material in enumerate(material_composition):
            cur.execute("""
                INSERT INTO formula_items (
                    uid, seq, material_code, concentration
                ) VALUES (%s, %s, %s, %s)
            """, (
                uid,
                idx + 1,  # Sequence starting from 1 for top row
                material["material_code"],
                material["concentration"]
            ))

        conn.commit()
        cur.close()
        conn.close()
        return uid

    except Exception as e:
        if conn:
            conn.rollback()
        cur.close()
        conn.close()
        raise e

