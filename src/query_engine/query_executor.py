import pymongo
from datetime import datetime
from typing import Dict, Any
import json

class MongoDBQueryExecutor:
    def __init__(self, db: pymongo.database.Database):
        """Initialize MongoDB query executor.

        Args:
            db: An active pymongo.database.Database instance.
        """
        if not isinstance(db, pymongo.database.Database):
            raise TypeError("db must be a valid pymongo.database.Database instance")
        self.db = db

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

                # Check Datetime
                filter_criteria = self._convert_iso_strings_to_datetime(filter_criteria)

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

                # Check Datetime
                pipeline = self._convert_iso_strings_to_datetime(pipeline)

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


    def is_iso_format(self, field):
        """
        Controlla se una stringa è un formato data/ora ISO 8601 valido.

        Args:
            stringa_da_controllare (str): La stringa da verificare.

        Returns:
            bool: True se la stringa è un formato data/ora ISO 8601 valido, False altrimenti.
        """
        try:
            datetime.fromisoformat(field)
            return True
        except Exception as e:
            return False

    def _convert_iso_strings_to_datetime(self, data):

        # Dictionary Case
        if isinstance(data, dict):
            converted_data={}

            for key, value in data.items():
                if isinstance(value, str) and self.is_iso_format(value):
                    converted_data[key] = datetime.fromisoformat(value)
                elif isinstance(value, (dict, list)):
                    converted_data[key] = self._convert_iso_strings_to_datetime(value)
                else:
                    converted_data[key] = value

            return converted_data

        # List Case
        elif isinstance(data, list):
            return [self._convert_iso_strings_to_datetime(item) for item in data]
        else:
            return data

# Helper function for direct execution
def execute_mongodb_query(db: pymongo.database.Database, query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a MongoDB query.

    Args:
        db: An active pymongo.database.Database instance
        query_dict: MongoDB query dictionary to execute

    Returns:
        Dictionary with query results
    """
    executor = MongoDBQueryExecutor(db)
    return executor.execute_query(query_dict)