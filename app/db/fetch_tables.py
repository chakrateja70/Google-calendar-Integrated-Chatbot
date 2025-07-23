from database import get_db_connection

if __name__ == "__main__":
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(table[0])
    cursor.close()
    conn.close() 