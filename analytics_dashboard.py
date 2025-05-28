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

# ---------- Analytics functions --------------------------
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
    

def get_distribuzione_comune_di_nascita(db):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed."
    pipeline = [
        {"$match": {"COMUNE_DI_NASCITA": {"$ne": None, "$exists": True}}},
        {"$group": {"_id":"$COMUNE_DI_NASCITA", "count":{"$sum": 1}}},
        {"$project": {"Comune di nascita": "$_id", "Numero Pazienti": "$count", "_id": 0}},
        {"$sort": {"Numero Pazienti": -1}},
        {"$limit": 20}
    ]
    try:
        result = list(db.ANAGRAFICA.aggregate(pipeline))
        return pd.DataFrame(result), None
    except Exception as e:
        return pd.DataFrame(), f"Error executing query comune di nascita: {e}"
    
def get_principali_cause_decesso(db):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed."
    pipeline = [
        {"$match": 
            {
            "DATA_DECESSO": {"$ne": None, "$exists": True},
            "MOTIVO_DECESSO": {"$ne": None, "$exists": True}
            }
        },
        {"$group": {"_id": "$MOTIVO_DECESSO", "count": {"$sum": 1}}},
        {"$project": {"Motivo del decesso": "$_id", "Numero Pazienti deceduti": "$count", "_id": 0}},
        {"$sort": {"Numero Pazienti deceduti": -1}},
        {"$limit": 20}
    ]
    try:
        result = list(db.ANAGRAFICA.aggregate(pipeline))
        return pd.DataFrame(result), None
    except Exception as e: 
        return pd.DataFrame(), f"Error executing query motivi di decesso: {e}"
    
def get_pazienti_per_evento(db):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed."
    pipeline = [
        {"$group": {"_id": "$TIPO_EVENTO", "count": {"$sum": 1}}},
        {"$project": {"Tipo evento": "$_id", "Numero Pazienti": "$count", "_id": 0}},
        {"$sort": {"Numero Pazienti": -1}}
    ]
    try:
        result = list(db.LISTA_EVENTI.aggregate(pipeline))
        return pd.DataFrame(result), None
    except Exception as e: 
        return pd.DataFrame(), f"Error executing query motivi di decesso: {e}"
    
# ------- Functions for medical records ---------------     
def get_lista_eventi(db, search_data: dict):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed"
    elif search_data is None:
        return pd.DataFrame(), "Invalid data to find the patient"
    else:

        # Inizializza la fase di match specifica
        match_stage = {}

        if search_data["type"] == "fiscal_code":
            match_stage = {"$match": {"CODICE_FISCALE": search_data["value"]}}
        elif search_data["type"] == 'code_section':
            id_paz = str(search_data['section']) + "_" + str(search_data['code'])
            match_stage = {"$match": {"ID_PAZ": id_paz}}
        else:
            return pd.DataFrame(), "Tipo di ricerca non valido."

        common_pipeline = [
            {"$project": {"ID_PAZ": 1, "_id": 0}},
            {"$lookup": {
                "from": "LISTA_EVENTI",          
                "localField": "ID_PAZ",          
                "foreignField": "ID_PAZ",        
                "as": "associated_events"        
            }},
            {"$unwind": "$associated_events"},
            {"$replaceRoot": {"newRoot": "$associated_events"}},
            {"$project": {
                "Id Paziente": "$ID_PAZ",        
                "Codice paziente": "$CODPAZ",    
                "Tipo evento": "$TIPO_EVENTO",   
                "Data evento": "$DATA",          
                "_id": 0                         
            }}
        ]

        pipeline = [match_stage] + common_pipeline

        try:
            result = list(db.ANAGRAFICA.aggregate(pipeline))

            if not result:
                return pd.DataFrame(), f"Nessun evento trovato per i dati inseriti"
            return pd.DataFrame(result), None
        except Exception as e:
            return pd.DataFrame(), f"Error during query event_list"

def get_most_worth_from_anamnesi(db, search_data: dict):
    if db is None:
        return pd.DataFrame(), "Connection to the database failed"
    elif search_data is None:
        return pd.DataFrame(), "Invalid data to find the patient"
    else:

        match_stage = {}

        if search_data["type"] == "fiscal_code":
            match_stage = {"$match": {"CODICE_FISCALE": search_data["value"]}}
        elif search_data["type"] == 'code_section':
            id_paz = str(search_data['section']) + "_" + str(search_data['code'])
            match_stage = {"$match": {"ID_PAZ": id_paz}}
        else:
            return pd.DataFrame(), "Tipo di ricerca non valido."
        

        common_pipeline = [

        ]

        pass