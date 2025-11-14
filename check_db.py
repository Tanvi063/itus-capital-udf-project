# check_db.py
import os
import sqlite3
from pathlib import Path

def check_database():
    db_path = Path("database/ttm_pat_yoy_growth.db").absolute()
    print(f"🔍 Checking database at: {db_path}")
    
    # Check if database exists
    if not db_path.exists():
        print("❌ Database file not found!")
        print("\nCurrent directory structure:")
        print(f"📂 {Path.cwd()}")
        for item in Path.cwd().iterdir():
            print(f"  - {item.name}/" if item.is_dir() else f"  {item.name}")
        
        if (Path.cwd() / "database").exists():
            print("\n📂 Database directory contents:")
            for item in (Path.cwd() / "database").iterdir():
                print(f"  - {item.name}")
        return False
    
    print("✅ Database file exists")
    
    # Check database contents
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in the database!")
            return False
        
        print("\n📊 Database tables found:")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("  Columns:")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
            
            # Show first few rows
            if count > 0:
                print("\n  Sample data (first 3 rows):")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                for row in cursor.fetchall():
                    print(f"    {row}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("DATABASE INTEGRITY CHECK".center(50))
    print("="*50)
    
    if check_database():
        print("\n" + "="*50)
        print("DATABASE CHECK COMPLETE - NO ISSUES FOUND".center(50))
        print("="*50)
    else:
        print("\n" + "="*50)
        print("DATABASE CHECK FAILED - ISSUES DETECTED".center(50))
        print("="*50)