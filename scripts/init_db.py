import os
import sys
import csv
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

# Add the parent directory to the Python path to allow sibling imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Configuration ---
# Set the path to your sample data directory relative to the project root
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "Industrial_DB_sample"

def get_db_connection():
    """Establishes and returns a database connection."""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ConnectionError("DATABASE_URL environment variable not set.")
    return psycopg2.connect(db_url)

def create_table_from_csv(cursor, table_name: str, csv_path: Path):
    """Dynamically creates a table based on a CSV file's header."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # Naively infer column types as TEXT for simplicity. 
        # A more advanced script could try to infer numeric, date types, etc.
        columns = [f'"{col.lower()}" TEXT' for col in header]
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {', '.join(columns)}
        );
        """
        print(f"  - Executing CREATE TABLE for '{table_name}'...")
        cursor.execute(create_sql)
        print(f"  - Table '{table_name}' created or already exists.")

def copy_data_from_csv(cursor, table_name: str, csv_path: Path):
    """Efficiently copies data from a CSV file to the specified table."""
    # Check if table is empty before copying
    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
    if cursor.fetchone()[0] > 0:
        print(f"  - Table '{table_name}' already contains data. Skipping COPY.")
        return

    print(f"  - Copying data from '{csv_path.name}' to '{table_name}'...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Use COPY FROM for high performance, skipping the header row.
        cursor.copy_expert(f"COPY \"{table_name}\" FROM STDIN WITH CSV HEADER", f)
    print(f"  - Data copy for '{table_name}' complete.")


def initialize_database():
    """
    Scans a directory for CSV files, creates a corresponding table for each,
    and populates it with the data from the CSV.
    """
    if not SAMPLE_DATA_DIR.exists():
        print(f"Error: Sample data directory not found at '{SAMPLE_DATA_DIR}'")
        return

    conn = None
    try:
        conn = get_db_connection()
        print("✅ Database connected successfully.")
        
        with conn.cursor() as cur:
            csv_files = list(SAMPLE_DATA_DIR.glob("*.csv"))
            print(f"Found {len(csv_files)} CSV files to process.")

            for csv_file in csv_files:
                # Sanitize the filename to use as a table name
                table_name = csv_file.stem.lower()
                print(f"\nProcessing file: '{csv_file.name}' -> Table: '{table_name}'")
                
                # 1. Create table based on CSV header
                create_table_from_csv(cur, table_name, csv_file)

                # 2. Copy data from CSV to the new table
                copy_data_from_csv(cur, table_name, csv_file)

        conn.commit()
        print("\n✅ Database initialization complete.")

    except (Exception, psycopg2.Error) as error:
        print(f"❌ An error occurred during database initialization: {error}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    initialize_database() 