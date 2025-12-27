import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'app', 'skud.db')

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Connected to database at {DB_PATH}")

    # Check controllers table
    cursor.execute("PRAGMA table_info(controllers)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"Current controllers columns: {columns}")
    
    if 'addr' not in columns:
        print("Adding addr to controllers...")
        try:
            cursor.execute("ALTER TABLE controllers ADD COLUMN addr INTEGER")
        except Exception as e:
            print(f"Error adding addr: {e}")
    else:
        print("Column 'addr' already exists in controllers.")

    if 'last_session' not in columns:
        print("Adding last_session to controllers...")
        try:
            cursor.execute("ALTER TABLE controllers ADD COLUMN last_session DATETIME")
        except Exception as e:
            print(f"Error adding last_session: {e}")
    else:
        print("Column 'last_session' already exists in controllers.")

    if 'extra_data' not in columns:
        print("Adding extra_data to controllers...")
        try:
            cursor.execute("ALTER TABLE controllers ADD COLUMN extra_data TEXT")
        except Exception as e:
            print(f"Error adding extra_data: {e}")
    else:
        print("Column 'extra_data' already exists in controllers.")

    # Check converters table
    cursor.execute("PRAGMA table_info(converters)")
    conv_columns = [info[1] for info in cursor.fetchall()]
    print(f"Current converters columns: {conv_columns}")

    if 'extra_data' not in conv_columns:
        print("Adding extra_data to converters...")
        try:
            cursor.execute("ALTER TABLE converters ADD COLUMN extra_data TEXT")
        except Exception as e:
            print(f"Error adding extra_data: {e}")
    else:
        print("Column 'extra_data' already exists in converters.")

    conn.commit()
    conn.close()
    print("Schema update completed.")

if __name__ == "__main__":
    fix_schema()
