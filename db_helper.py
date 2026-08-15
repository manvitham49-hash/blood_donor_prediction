def save_to_db_from_df(row):
    import pymysql
    from datetime import datetime

    conn = None
    cursor = None

    try:
        print("🔥 FUNCTION CALLED")

        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="root123",
            database="blood_donor_db"
        )
        cursor = conn.cursor()

        donor_id = str(row.get("donor_id", "")).strip()

        if not donor_id:
            print("❌ ERROR: donor_id missing")
            return

        def clean(val, col=None):
            if val is None:
                return None

            val = str(val).strip()

            if val.lower() == "nan" or val == "":
                return None

            # ✅ FIX DATE FORMAT
            if col in ["created_at", "date_of_birth", "last_blood_donation_date"]:
                try:
                    return datetime.strptime(val, "%m/%d/%Y").strftime("%Y-%m-%d")
                except:
                    return None

            return val

        # ✅ ONLY include columns that exist AND have value
        columns = [col for col in row.index if col != "donor_id"]

        if not columns:
            print("⚠️ No columns to update")
            return

        set_clause = ", ".join([f"{col}=%s" for col in columns])
        values = [clean(row[col], col) for col in columns]

        query = f"""
        UPDATE donors
        SET {set_clause}
        WHERE donor_id = %s
        """

        print("🧾 QUERY:", query)
        print("📦 VALUES:", values + [donor_id])

        cursor.execute(query, values + [donor_id])
        conn.commit()

        print("✅ ROWS UPDATED:", cursor.rowcount)

        if cursor.rowcount == 0:
            print("⚠️ WARNING: No row matched donor_id")

    except Exception as e:
        print("❌ ERROR:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()