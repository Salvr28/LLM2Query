import pymongo
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import config

def get_db_connection():
    """Get a connection to the MongoDB database."""
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[config.MONGO_DB_NAME]
        return db
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print("Failed to connect to MongoDB server: {e}")
        return None
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Analytics functions
def get_distibuzione_sesso(db):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed."
    pipeline = [
        {"$group": {"_id": "$SESSO", "count": {"$sum": 1}}},
        {"$project": {"Sesso": "$_id", "Numero Pazienti": "$count", "_id": 0}},
        {"$sort": {"Numero Pazienti": -1}}
    ]
    try:
        result = list(db.ANAGRAFICA.aggregate(pipeline))
        return pd.DataFrame(result), None
    except Exception as e:
        return pd.DataFrame(), f"Error executing query sesso: {e}"