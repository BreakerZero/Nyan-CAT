import sqlite3

try:
    conn = sqlite3.connect('database/nyan.db')  # replace with your db path
    print("Database opened successfully!")
    conn.close()
except sqlite3.OperationalError as e:
    print("Couldn't open database. Error:", e)

