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
    
    def execute_query(self, query_dict: Dict[str, Any]) -> Dict[str, Any]:
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
            "query_executed": json.dumps(query_dict),
            "query_type": None,
            "affected_count": 0
        }
        
        try:

            collection_name = query_dict.get('collection_name')
            operation_type = query_dict.get('operation_type')
            arguments = query_dict.get('arguments',{})

            if not collection_name:
                raise ValueError('collection_name is required')
            collection = self.db[collection_name]

            # Operation FIND
            if operation_type == 'find':
                result['query_type'] = 'find'
                filter_criteria = arguments.get('filter', {})
                projection = arguments.get('projection')
                if projection:
                    cursor = collection.find(filter_criteria, projection)
                else: 
                    cursor = collection.find(filter_criteria)
                result_data = list(cursor)
                result['data'] = self._sanitize_data(result_data)
                result['affected_count'] = len(result_data)
                result['success'] = True

                
            # Operation AGGREGATE
            elif operation_type == 'aggregate':
                result['query_type'] = 'aggregate'
                pipeline = arguments.get('pipeline', [])
                cursor = collection.aggregate(pipeline)
                result_data = list(cursor)
                result['data'] = self._sanitize_data(result_data)
                result['affected_count'] = len(result_data)
                result['success'] = True
            
            else:
                raise ValueError(f"Unsupported operation type: {operation_type}")
            


        except Exception as e:
            result['error'] = str(e)
            return result
        
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
def execute_mongodb_query(query_dict: Dict[str, Any], connection_string: str, db_name: str) -> Dict[str, Any]:
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
        return executor.execute_query(query_dict)
    finally:
        executor.close()