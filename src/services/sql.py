import mysql.connector

conn = mysql.connector.connect(
    host="192.168.0.108",
    port=3306,
    user="root",
    password="123",
    database="Frapa"
)

cursor = conn.cursor()

cursor.execute("SHOW TABLES")

for table in cursor:
    print(table)