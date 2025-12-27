import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'app', 'skud.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, name, addr, last_session FROM controllers LIMIT 5")
rows = cursor.fetchall()

print("Current data in controllers table:")
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Addr: {row[2]}, LastSession: {row[3]}")

conn.close()
