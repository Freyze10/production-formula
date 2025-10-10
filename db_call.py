import psycopg2


def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="db_formula",
        user="postgres",
        password="password",
        port="5433"
    )


def get_formula_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT uid, formula_index, customer, product_code, product_color, total_concentration, dosage 
                    FROM formula_primary
                    ORDER BY uid DESC """)
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

