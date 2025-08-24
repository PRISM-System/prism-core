from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DatabaseQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    params: Optional[List[Any]] = Field(None, description="Query parameters")

class DatabaseQueryResponse(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Query results")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: Optional[float] = Field(None, description="Query execution time in milliseconds")
    
class TableListResponse(BaseModel):
    tables: List[str] = Field(..., description="List of available tables")

class TableSchemaResponse(BaseModel):
    table_name: str = Field(..., description="Name of the table")
    columns: List[Dict[str, str]] = Field(..., description="Column information (name, type, nullable, etc.)")

class DatabaseStatsResponse(BaseModel):
    total_tables: int = Field(..., description="Total number of tables")
    database_size: str = Field(..., description="Database size")
    connection_status: str = Field(..., description="Database connection status")

class TableDataRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to query")
    limit: Optional[int] = Field(10, description="Maximum number of rows to return")
    offset: Optional[int] = Field(0, description="Number of rows to skip")
    where_clause: Optional[str] = Field(None, description="WHERE clause conditions")
    order_by: Optional[str] = Field(None, description="ORDER BY clause") 