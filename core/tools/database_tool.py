import time
from typing import Any, Dict, Optional
from .base import BaseTool
from .schemas import ToolRequest, ToolResponse
from ..data.service import DatabaseService


class DatabaseTool(BaseTool):
    """Tool for querying the industrial database."""
    
    def __init__(self, db_service: DatabaseService):
        """Initialize DatabaseTool with database service."""
        
        parameters_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["query", "list_tables", "get_table_schema", "get_table_data"],
                    "description": "Action to perform on the database"
                },
                "query": {
                    "type": "string",
                    "description": "SQL query to execute (only SELECT statements allowed)"
                },
                "table_name": {
                    "type": "string",
                    "description": "Name of the table for table-specific operations"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of rows to return for table data queries"
                },
                "offset": {
                    "type": "integer", 
                    "default": 0,
                    "description": "Number of rows to skip for pagination"
                },
                "where_clause": {
                    "type": "string",
                    "description": "WHERE clause for filtering data"
                },
                "order_by": {
                    "type": "string",
                    "description": "ORDER BY clause for sorting data"
                }
            },
            "required": ["action"]
        }
        
        super().__init__(
            name="database_tool",
            description="Tool for querying industrial manufacturing database. Can execute SELECT queries, list tables, get table schemas, and retrieve table data with filtering.",
            parameters_schema=parameters_schema
        )
        
        self.db_service = db_service
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute database operation."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(request.parameters):
                return ToolResponse(
                    success=False,
                    error_message="Invalid parameters provided"
                )
            
            action = request.parameters["action"]
            
            if action == "query":
                result = await self._execute_query(request.parameters)
            elif action == "list_tables":
                result = await self._list_tables()
            elif action == "get_table_schema":
                result = await self._get_table_schema(request.parameters)
            elif action == "get_table_data":
                result = await self._get_table_data(request.parameters)
            else:
                return ToolResponse(
                    success=False,
                    error_message=f"Unknown action: {action}"
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResponse(
                success=True,
                result=result,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResponse(
                success=False,
                error_message=str(e),
                execution_time_ms=round(execution_time, 2)
            )
    
    async def _execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom SQL query."""
        query = params.get("query")
        if not query:
            raise ValueError("Query parameter is required for query action")
        
        # Security check - only allow SELECT statements
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed for security reasons")
        
        result = self.db_service.execute_query_with_timing(query)
        return {
            "data": result.data,
            "row_count": result.row_count,
            "execution_time_ms": result.execution_time_ms
        }
    
    async def _list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        result = self.db_service.get_tables()
        return {"tables": result.tables}
    
    async def _get_table_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema for a specific table."""
        table_name = params.get("table_name")
        if not table_name:
            raise ValueError("table_name parameter is required for get_table_schema action")
        
        result = self.db_service.get_table_schema(table_name)
        return {
            "table_name": result.table_name,
            "columns": result.columns
        }
    
    async def _get_table_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get data from a specific table."""
        table_name = params.get("table_name")
        if not table_name:
            raise ValueError("table_name parameter is required for get_table_data action")
        
        result = self.db_service.get_table_data(
            table_name=table_name,
            limit=params.get("limit", 10),
            offset=params.get("offset", 0),
            where_clause=params.get("where_clause"),
            order_by=params.get("order_by")
        )
        
        return {
            "data": result.data,
            "row_count": result.row_count,
            "execution_time_ms": result.execution_time_ms
        } 