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
        SELECT uid, formula_index, formula_date, customer, product_code, product_color, dosage, ld
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
    if record and record[0] is not None:
        return record[0], record[1]
    return None, None


def get_formula_latest_uid():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT MAX(uid)
                    FROM formula_primary""")
    record = cur.fetchone()

    cur.close()
    conn.close()
    return record


def get_rm_code_lists():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT rm_code
                    FROM tbl_rm_warehouse 
                    ORDER BY rm_code ASC""")
    records = cur.fetchall()

    cur.close()
    conn.close()
    if records:
        return [row[0] for row in records]
    else:
        return []


def save_formula(primary_data, material_composition):
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Insert into formula_primary - using all fields from primary_data
        cur.execute("""
            INSERT INTO formula_primary (
                uid, formula_index, customer, product_code, product_color, 
                dosage, ld, mix_type, resin, application, 
                cm_num, cm_date, remarks, total_concentration, mb_dc, html_code, c, m, y, k, 
                matched_by, encoded_by, formula_date, dbf_updated_by, dbf_updated_on_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING uid;
        """, (
            primary_data["uid"],
            primary_data["formula_index"],
            primary_data["customer"],
            primary_data["product_code"],
            primary_data["product_color"],
            primary_data["dosage"],
            primary_data["ld"],
            primary_data["mix_type"],
            primary_data["resin"],
            primary_data["application"],
            primary_data["cm_num"],
            primary_data["cm_date"],
            primary_data["remarks"],
            primary_data["total_concentration"],
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


def update_formula(primary_data, material_composition):
    conn = get_connection()
    try:
        cur = conn.cursor()

        # --- Update formula_primary ---
        cur.execute("""
            UPDATE formula_primary
            SET
                formula_index = %s,
                customer = %s,
                product_code = %s,
                product_color = %s,
                total_concentration = %s,
                dosage = %s,
                ld = %s,
                mix_type = %s,
                resin = %s,
                application = %s,
                cm_num = %s,
                cm_date = %s,
                remarks = %s,
                mb_dc = %s,
                html_code = %s,
                c = %s,
                m = %s,
                y = %s,
                k = %s,
                matched_by = %s,
                encoded_by = %s,
                formula_date = %s,
                dbf_updated_by = %s,
                dbf_updated_on_text = %s
            WHERE uid = %s;
        """, (
            primary_data["formula_index"],
            primary_data["customer"],
            primary_data["product_code"],
            primary_data["product_color"],
            primary_data["total_concentration"],
            primary_data["dosage"],
            primary_data["ld"],
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
            primary_data["dbf_updated_on_text"],
            primary_data["uid"]  # used to locate which row to update
        ))

        # --- Replace material compositions ---
        # Delete existing records for this uid
        cur.execute("DELETE FROM formula_items WHERE uid = %s;", (primary_data["uid"],))

        # Insert updated materials
        for idx, material in enumerate(material_composition):
            cur.execute("""
                INSERT INTO formula_items (uid, seq, material_code, concentration)
                VALUES (%s, %s, %s, %s);
            """, (
                primary_data["uid"],
                idx + 1,
                material["material_code"],
                material["concentration"]
            ))

        conn.commit()
        cur.close()
        conn.close()
        return primary_data["uid"]

    except Exception as e:
        if conn:
            conn.rollback()

        cur.close()
        conn.close()
        raise e


# Production calls


def get_formula_select(product_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT formula_index, uid, customer, product_code, product_color, dosage, ld
        FROM formula_primary
        WHERE product_code = %s 
        ORDER BY uid DESC
    """, (product_code,))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


def get_single_production_data(prod_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM formula_primary
        WHERE prod_id = %s
    """, (prod_id,))

    records = cur.fetchone()
    cur.close()
    conn.close()
    return records


def get_all_production_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT prod_id, production_date, customer, product_code, product_color, lot_number, qty_produced 
        FROM production_primary
        ORDER BY prod_id DESC
    """)

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


def get_single_production_details(prod_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT material_code, large_scale, small_scale, total_weight, total_loss, total_consumption 
        FROM production_items
        WHERE material_code != '' AND prod_id = %s
        ORDER BY seq ASC;
    """, (prod_id,))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

