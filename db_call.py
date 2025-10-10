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
        SELECT uid, formula_index, customer, product_code, product_color, total_concentration, dosage
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

    cur.execute("SELECT material_code, concentration FROM public.formula_items WHERE uid = %s ORDER BY seq DESC",
                (uid,))
    records = cur.fetchall()

    cur.close()
    conn.close()
    return records


def get_min_max_formula_date():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT MIN(formula_date) AS earliest_date,
                            MAX(formula_date) AS latest_date
                    FROM formula_primary""")
    records = cur.fetchone()

    cur.close()
    conn.close()
    return records

