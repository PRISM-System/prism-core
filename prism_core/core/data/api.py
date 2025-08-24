from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from .service import DatabaseService
from .schemas import (
    DatabaseQueryRequest,
    DatabaseQueryResponse,
    TableListResponse,
    TableSchemaResponse,
    DatabaseStatsResponse,
    TableDataRequest
)

def create_db_router(db_service: DatabaseService) -> APIRouter:
    """Create a FastAPI router for database operations."""
    router = APIRouter(prefix="/db", tags=["database"])
    
    def get_db_service():
        return db_service
    
    @router.get("/", response_model=DatabaseStatsResponse)
    async def get_database_info(db: DatabaseService = Depends(get_db_service)):
        """Get general database information and statistics."""
        try:
            return db.get_database_stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get database info: {str(e)}")
    
    @router.get("/tables", response_model=TableListResponse)
    async def list_tables(db: DatabaseService = Depends(get_db_service)):
        """Get list of all tables in the database."""
        try:
            return db.get_tables()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")
    
    @router.get("/tables/{table_name}/schema", response_model=TableSchemaResponse)
    async def get_table_schema(
        table_name: str, 
        db: DatabaseService = Depends(get_db_service)
    ):
        """Get schema information for a specific table."""
        try:
            return db.get_table_schema(table_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Table not found or error: {str(e)}")
    
    @router.get("/tables/{table_name}/data", response_model=DatabaseQueryResponse)
    async def get_table_data(
        table_name: str,
        limit: int = Query(10, ge=1, le=1000, description="Maximum number of rows to return"),
        offset: int = Query(0, ge=0, description="Number of rows to skip"),
        where_clause: Optional[str] = Query(None, description="WHERE clause conditions"),
        order_by: Optional[str] = Query(None, description="ORDER BY clause"),
        db: DatabaseService = Depends(get_db_service)
    ):
        """Get data from a specific table with filtering and pagination."""
        try:
            return db.get_table_data(
                table_name=table_name,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by=order_by
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")
    
    @router.post("/query", response_model=DatabaseQueryResponse)
    async def execute_query(
        request: DatabaseQueryRequest,
        db: DatabaseService = Depends(get_db_service)
    ):
        """Execute a custom SQL query."""
        try:
            # Basic security check - only allow SELECT statements
            query_upper = request.query.strip().upper()
            if not query_upper.startswith('SELECT'):
                raise HTTPException(
                    status_code=400, 
                    detail="Only SELECT queries are allowed for security reasons"
                )
            
            return db.execute_query_with_timing(request.query, request.params)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")
    
    @router.post("/tables/{table_name}/query", response_model=DatabaseQueryResponse)
    async def query_table(
        table_name: str,
        request: TableDataRequest,
        db: DatabaseService = Depends(get_db_service)
    ):
        """Query a specific table with advanced filtering options."""
        try:
            return db.get_table_data(
                table_name=request.table_name or table_name,
                limit=request.limit,
                offset=request.offset,
                where_clause=request.where_clause,
                order_by=request.order_by
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Table query failed: {str(e)}")
    
    return router 