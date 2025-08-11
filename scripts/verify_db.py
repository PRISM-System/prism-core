import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path to allow sibling imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data.postgresql import PostgreSQLDataStore

def verify_database_contents():
    """
    Connects to the database and fetches all records from the 'events' table.
    """
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)

    print("Connecting to the database to verify contents...")
    try:
        db = PostgreSQLDataStore(db_url)
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        sys.exit(1)

    try:
        print("\n--- Verifying 'events' table ---")
        events = db.query("SELECT * FROM events ORDER BY id;")
        
        if not events:
            print("❌ Verification failed: The 'events' table is empty.")
            print("   Please run 'python scripts/init_db.py' first.")
            return

        print(f"✅ Verification successful. Found {len(events)} records:")
        for event in events:
            print(f" - ID: {event['id']}, Type: {event['event_type']}, Severity: {event['severity']}, Desc: {event['description']}")
            
    except Exception as e:
        print(f"An error occurred during verification: {e}")
    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    verify_database_contents() 