import pymongo
from typing import Dict, List, Any, Union, Optional
import json

class MongoDBQueryExecutor:
    def __init__(self, connection_string: str, db_name: str):
        """Initialize MongoDB query executor.
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name to connect to
        """
        try:
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[db_name]
            # Test connection
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            raise ConnectionError("Failed to connect to MongoDB server")
        except pymongo.errors.OperationFailure as e:
            raise ConnectionError(f"Authentication failed: {str(e)}")
    
    def execute_query(self, query_str: str) -> Dict[str, Any]:
        """Execute a MongoDB query string.
        
        Args:
            query_str: MongoDB query string to execute
            
        Returns:
            Dictionary with query results and metadata
        """
        
        result = {
            "success": False,
            "data": None,
            "error": None,
            "query_executed": query_str,
            "query_type": None,
            "affected_count": 0
        }
        
        try:
            # Create a safe execution environment
            exec_globals = {
                "db": self.db,
                "list": list,
                "result_data": None,
                "affected_count": 0,
                "query_type": None
            }


            # Exec MongoDB query to obtain cursor
         #   cursor = eval(query_str, exec_globals)
            
        #    if isinstance(cursor, pymongo.cursor.Cursor):
       #         result_data = list(cursor)
      #          if "find(" in query_str:
     #               result["query_type"] = 'find'
    #            elif "aggreagate(" in query_str:
   #                 result["query_type"] = 'aggregate'
  #              else:
 #                   result['query_type'] = 'generic-cursor'
#
 #           else:
#                result_data = cursor
#                result['query_type']='other'
#                result['affected_count']=0




            # Determine query type and prepare execution code
            if "find(" in query_str:
                exec_code = f"result_data = list({query_str})\nquery_type = 'find'\naffected_count = len(result_data)"
            elif "aggregate(" in query_str:
                exec_code = f"result_data = list({query_str})\nquery_type = 'aggregate'\naffected_count = len(result_data)"
            else:
                exec_code = f"result_data = {query_str}\nquery_type = 'other'"
            
            # Execute the query
            exec(exec_code, exec_globals)
            
            # Extract results
            result["success"] = True
            result["data"] = self._sanitize_data(exec_globals["result_data"])
            result["query_type"] = exec_globals["query_type"]
            result["affected_count"] = exec_globals["affected_count"]
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize MongoDB data for JSON serialization.
        
        Args:
            data: Data to sanitize
            
        Returns:
            JSON-serializable data
        """
        if data is None:
            return None
            
        if isinstance(data, (str, int, float, bool)):
            return data
            
        if isinstance(data, dict):
            # Convert ObjectId to string, etc.
            return {k: self._sanitize_data(v) for k, v in data.items()}
            
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
            
        # Handle MongoDB-specific types
        if hasattr(data, "__str__"):
            return str(data)
            
        return repr(data)
    
    def close(self):
        """Close the MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()
            
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()

# Helper function for direct execution
def execute_mongodb_query(query_str: str, connection_string: str, db_name: str) -> Dict[str, Any]:
    """Execute a MongoDB query.
    
    Args:
        query_str: MongoDB query string
        connection_string: MongoDB connection string
        db_name: Database name
        
    Returns:
        Dictionary with query results
    """
    executor = MongoDBQueryExecutor(connection_string, db_name)
    try:
        return executor.execute_query(query_str)
    finally:
        executor.close()