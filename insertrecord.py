import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="Elerning",
        user="mangesh",       # use admin to test
        password="Admin",
        port="5432",
        options="-c search_path=public"
    )

    print("✅ Connected to PostgreSQL successfully")

    cursor = conn.cursor()

    # ---------- INSERT QUERY ----------
    insert_query = """
        INSERT INTO tweets (tweet_id, user_id, msg, tweet_date)
        VALUES (%s, %s, %s, CURRENT_DATE)
    """

    data = (
        1,                          # tweet_id
        901,                         # user_id
        "Hello from psycopg2!",     # msg
        
    )

    cursor.execute(insert_query, data)
    conn.commit()   # 🔴 important to save changes

    print("✅ Data inserted successfully into tweets table")

except Exception as e:
    print("❌ Error:", e)

finally:
    if 'conn' in locals():
        conn.close()
        print("🔌 Connection closed")
