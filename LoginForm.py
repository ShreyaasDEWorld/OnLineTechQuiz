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
    cursor.execute("select * from tweets ")
    result = cursor.fetchone()

    if result:
        print("Test query result:", result)
    else:
        print("Table is empty")

except Exception as e:
    print("❌ Error:", e)

finally:
    if 'conn' in locals():
        conn.close()
        print("🔌 Connection closed")
