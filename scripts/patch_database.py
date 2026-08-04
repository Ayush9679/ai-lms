import sqlite3
import os

def patch_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping.")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check columns
        cursor.execute("PRAGMA table_info(assignments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "is_published" not in columns:
            cursor.execute("ALTER TABLE assignments ADD COLUMN is_published BOOLEAN DEFAULT 1")
            print(f"Added is_published to {db_path}")
        else:
            print(f"is_published already exists in {db_path}")
            
        if "is_closed" not in columns:
            cursor.execute("ALTER TABLE assignments ADD COLUMN is_closed BOOLEAN DEFAULT 0")
            print(f"Added is_closed to {db_path}")
        else:
            print(f"is_closed already exists in {db_path}")
            
        conn.commit()
        conn.close()
        print(f"Patched {db_path} successfully!")
    except Exception as e:
        print(f"Failed to patch {db_path}: {e}")

if __name__ == "__main__":
    patch_db("local_dev.db")
    patch_db("ai_lms.db")
    patch_db("test_ailms.db")
