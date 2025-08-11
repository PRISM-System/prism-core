import time
from typing import List, Dict, Any, Optional
from .postgresql import PostgreSQLDataStore
from .schemas import (
    DatabaseQueryResponse, 
    TableListResponse, 
    TableSchemaResponse, 
    DatabaseStatsResponse
)

class DatabaseService(PostgreSQLDataStore):
    """
    Enhanced database service for API operations.
    Extends PostgreSQLDataStore with additional functionality.
    """
    
    def execute_query_with_timing(self, query: str, params: Optional[List[Any]] = None) -> DatabaseQueryResponse:
        """Execute a query and return results with timing information."""
        start_time = time.time()
        
        try:
            # Convert params list to tuple if provided
            query_params = tuple(params) if params else None
            results = self.query(query, query_params)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return DatabaseQueryResponse(
                data=results,
                row_count=len(results),
                execution_time_ms=round(execution_time, 2)
            )
        except Exception as e:
            raise Exception(f"Database query failed: {str(e)}")
    
    def get_tables(self) -> TableListResponse:
        """Get list of all tables in the database."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        results = self.query(query)
        tables = [row['table_name'] for row in results]
        
        return TableListResponse(tables=tables)
    
    def get_table_schema(self, table_name: str) -> TableSchemaResponse:
        """Get schema information for a specific table."""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        results = self.query(query, (table_name,))
        
        columns = []
        for row in results:
            column_info = {
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'],
                'default': str(row['column_default']) if row['column_default'] else None,
                'max_length': str(row['character_maximum_length']) if row['character_maximum_length'] else None
            }
            columns.append(column_info)
        
        return TableSchemaResponse(
            table_name=table_name,
            columns=columns
        )
    
    def get_database_stats(self) -> DatabaseStatsResponse:
        """Get general database statistics."""
        # Get table count
        table_count_query = """
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
        """
        table_count_result = self.query(table_count_query)
        total_tables = table_count_result[0]['count'] if table_count_result else 0
        
        # Get database size
        size_query = """
        SELECT pg_size_pretty(pg_database_size(current_database())) as size;
        """
        size_result = self.query(size_query)
        database_size = size_result[0]['size'] if size_result else "Unknown"
        
        return DatabaseStatsResponse(
            total_tables=total_tables,
            database_size=database_size,
            connection_status="Connected"
        )
    
    def get_table_data(self, table_name: str, limit: int = 10, offset: int = 0, 
                      where_clause: Optional[str] = None, order_by: Optional[str] = None) -> DatabaseQueryResponse:
        """Get data from a specific table with filtering and pagination."""
        
        # Build the query
        query_parts = [f"SELECT * FROM {table_name}"]
        params = []
        
        if where_clause:
            query_parts.append(f"WHERE {where_clause}")
        
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        else:
            # Default ordering by first column if no order specified
            query_parts.append("ORDER BY 1")
        
        query_parts.append(f"LIMIT {limit} OFFSET {offset}")
        
        query = " ".join(query_parts)
        
        return self.execute_query_with_timing(query, params) 