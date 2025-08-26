from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import DictCursor

from .base import BaseDataStore
from ..config import settings # Assuming DB settings will be in config

class PostgreSQLDataStore(BaseDataStore):
    """
    A data store implementation for PostgreSQL.
    """
    def __init__(self, db_url: str):
        """
        Initializes the connection to the PostgreSQL database.
        
        Args:
            db_url: The database connection URL (e.g., "postgresql://user:password@host:port/dbname").
        """
        self.conn = psycopg2.connect(db_url)
        # Ensure a failed statement doesn't poison subsequent commands
        self.conn.autocommit = True

    def _execute(self, query: str, params: tuple = None, fetch=None):
        """Helper method to execute queries with rollback on error."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            try:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                # autocommit mode: no explicit commit required
            except Exception:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                raise

    def add(self, data: Dict[str, Any], table_name: str) -> Any:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
        result = self._execute(query, tuple(data.values()), fetch="one")
        return result['id']

    def get(self, id: Any, table_name: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {table_name} WHERE id = %s"
        result = self._execute(query, (id,), fetch="one")
        return dict(result) if result else None

    def update(self, id: Any, data: Dict[str, Any], table_name: str) -> bool:
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        self._execute(query, tuple(data.values()) + (id,))
        return True # Should add more robust error handling

    def delete(self, id: Any, table_name: str) -> bool:
        query = f"DELETE FROM {table_name} WHERE id = %s"
        self._execute(query, (id,))
        return True # Should add more robust error handling

    def query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Executes a raw SQL query."""
        results = self._execute(query, params, fetch="all")
        return [dict(row) for row in results] if results else []

    def close(self):
        """Closes the database connection."""
        self.conn.close() 