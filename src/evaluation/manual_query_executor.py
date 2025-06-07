import os
import config
from pymongo import MongoClient
from src.query_engine.query_executor import MongoDBQueryExecutor
from typing import Dict, Any
import pandas as pd


# ---- Mongo Client Config ----
try:
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[config.MONGO_DB_NAME]

except Exception as e:
    print(f"Error Mongo DB configuration: {e}")

# ---- Query Executor -----
executor = MongoDBQueryExecutor(db)

# ---- Path for Gold Results ------
current_script_dir = os.path.dirname(os.path.abspath(__file__))
results_path = os.path.join(current_script_dir, "gold_results")

def gold_easy_query_n3():

    gold_json = {
        "collection_name": "ANAGRAFICA",
        "operation_type": "find",
        "arguments": {
            "filter": {
                "COMUNE_DI_NASCITA": "TEANO"
            },
            "projection": {
                "_id": 0
            }
        }
    }

    return gold_json

def gold_easy_query_n4():

    gold_json = {
        "collection_name": "ESAMI_SPECIALISTICI",
        "operation_type": "find",
        "arguments": {
            "filter": {
                "ID_PAZ": "1_7",
                "DATA": "2006-06-07T00:00:00.000+00:00"
            },
            "projection": {
                "FT3": 1,
                "FT4": 1,
                "TSH":  1,
                "_id": 0
            }
        }
    }

    return gold_json

def gold_easy_query_n5():

    """
    User Need: Mostra tutti dati di anamnesi del
    paziente con id paziente 1_7
    """

    gold_json = {
        "collection_name": "ANAMNESI",
        "operation_type": "find",
        "arguments": {
            "ID_PAZ": "1_7"
        },
        "projection": {
            "_id": 0
        }
    }

    return gold_json

def gold_medium_query_n11():

    """
    User Need: Trova nome, cognome e data di nascita dei
    pazienti di Teano che hanno avuto
    un infarto miocardico acuto pregresso
    """

    gold_json = {
        "collection_name": "ANAGRAFICA",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$lookup": {
                    "from": "ANAMNESI",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "an_data"
                }},
                {"$match": {
                    "COMUNE_DI_NASCITA": "TEANO",
                    "an_data.PREVIOUS_IMA": "YES"
                }},
                {"$project": {
                    "_id": 0,
                    "Nome Paziente": "$NOMEPAZ",
                    "Cognome Paziente": "$COGNOME",
                    "Data di nascita": "$DATADINASCITA",
                    "IMA": "$an_data.PREVIOUS_IMA"
                }}
            ]
        }
    }

    return gold_json

def gold_medium_query_n12():

    """
    User Need: Per ogni sezione conta quanti
    pazienti soffrono di diabete
    """

    gold_json = {
        "collection_name": "ANAMNESI",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$match": {
                    "DIABETE": "YES",
                }},
                {"$group": {
                    "_id": "$SEZIONE",
                    "count": {
                        "$sum": 1
                    }
                }},
                {"$sort": {
                    "count": -1
                }},
                {"$project": {
                    "Sezione": "$_id",
                    "Numero pazienti": "$count",
                    "_id": 0
                }}
            ]
        }
    }

    return gold_json

def gold_medium_query_n13():

    """
    User Need: Qual è il valore massimo di glicemia
    registrato per il paziente con id paziente 1_7
    """

    gold_json = {
        "collection_name": "ESAMI_LABORATORIO",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$match": {
                    "ID_PAZ": "1_7"
                }},
                {"$group": {
                    "_id": None,
                    "glicemiaMassima": {
                        "$max": "$GLICEMIA"
                    }
                }},
                {"$project": {
                    "Id Paziente": "1_7",
                    "Massima Glicemia": "$glicemiaMassima",
                    "_id": 0
                }}
            ]
        }
    }

    return gold_json

def gold_medium_query_n14():

    """
    User Need: Elenca  i primi 100
    pazienti (nome, cognome) che soffrono
    di insufficienza cardiaca
    """

    gold_json = {
        "collection_name": "ECOCARDIO_DATI",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$match": {
                    "HEART_FAILURE": "YES"
                }},
                {"$lookup": {
                    "from": "ANAGRAFICA",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "anagrafica_dati"
                }},
                {"$unwind": "$anagrafica_dati"},
                {"$group": {
                    "_id": "$ID_PAZ",
                    "Nome Paziente": {"$first": "$anagrafica_dati.NOMEPAZ"},
                    "Cognome Paziente": {"$first": "$anagrafica_dati.COGNOME"}
                }},
                {"$project": {
                    "_id": 0,
                    "Nome paziente": "$Nome Paziente",
                    "Cognome_paziente": "$Cognome Paziente",
                    "Insufficienza cardiaca": "YES"
                }},
                {"$limit": 100}
            ]
        }
    }

    return gold_json

def gold_medium_query_n15():

    """
    User Need: Mostra tutti gli esami del sangue
    per i pazienti nati dopo il 1990
    """

    gold_json = {
        "collection_name": "ANAGRAFICA",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$match": {
                    "DATADINASCITA": {
                        "$gt": "1990-01-01T00:00:00.000+00:00"
                    }
                }},
                {"$lookup": {
                    "from": "ESAMI_LABORATORIO",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "esami_data"
                }},
                {"$unwind": "$esami_data"},
                {"$project": {
                    "_id": 0,
                    "ID_PAZ": "$ID_PAZ",
                    "Nome Paziente": "$NOMEPAZ",
                    "Cognome Paziente": "$COGNOME",
                    "Data Esame": "$esami_data.DATA"
                }}
            ]
        }
    }

    return gold_json

def gold_difficult_query_n21():

    """
    User Need: Per i pazienti con una insufficienza cardiaca,
    calcola la media del loro BMI e la media del filtrato GFR
    """

    gold_json = {
        "collection_name": "ECOCARDIO_DATI",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {
                    "$match": {
                        "HEART_FAILURE": "YES"
                    }
                },
                {
                    "$lookup": {
                        "from": "ESAMI_LABORATORIO",
                        "localField": "ID_PAZ",
                        "foreignField": "ID_PAZ",
                        "as": "esami_lab"
                    }
                },
                {
                    "$unwind": {
                        "path": "$esami_lab",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_bmi": {
                            "$avg": "$PESO"
                        },
                        "avg_gfr": {
                            "$avg": "$esami_lab.FILTRATO_GFR"
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "avg_bmi": 1,
                        "avg_gfr": 1
                    }
                }
            ]
        }
    }

    return gold_json

def gold_difficult_query_n22():

    """
    User Need: Per ogni paziente di Napoli che soffre di diabete e di insufficienza cardiaca,
    mostrami l’id paziente, il cognome ed il nome con valore medio di
    glicemia e valore medio di EF. Ordina per cognome.
    """

    gold_json = {
        "collection_name": "ANAGRAFICA",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {"$match": {
                    "COMUNE_DI_NASCITA": "NAPOLI"
                }},
                {"$lookup": {
                    "from": "ANAMNESI",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "an_data"
                }},
                {"$unwind": "$an_data"},
                {"$match": {
                    "an_data.DIABETE": "YES"
                }},
                {"$lookup": {
                    "from": "ECOCARDIO_DATI",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "eco_data"
                }},
                {"$unwind": "$eco_data"},
                {"$match": {
                    "eco_data.HEART_FAILURE": "YES"
                }},
                {"$lookup": {
                    "from": "ESAMI_LABORATORIO",
                    "localField": "ID_PAZ",
                    "foreignField": "ID_PAZ",
                    "as": "lab_data"
                }},
                {"$unwind": "$lab_data"},
                {"$group": {
                    "_id": {
                        "ID_PAZ": "$ID_PAZ",
                        "Nome Paziente": "$NOMEPAZ",
                        "Cognome Paziente": "$COGNOME"
                    },
                    "avg_glicemia": {
                        "$avg": "$lab_data.GLICEMIA"
                    },
                    "avg_ef": {
                        "$avg": "$eco_data.EF"
                    }
                }},
                {"$projection": {
                    "_id": 0,
                    "ID_PAZ": "$_id.ID_PAZ",
                    "cognome": "$_id.Cognome Paziente",
                    "nome": "$_id.Nome Paziente",
                    "avg_glicemia": 1,
                    "avg_ef": 1
                }},
                {"$sort": {
                    "cognome": 1
                }}

            ]
        }
    }


    return gold_json

def gold_difficult_query_n23():

    """
    User Need: Per ogni sezione trova il paziente con il BMI più
    alto registrato ed il paziente con filtrato GFR più basso.
    """

    gold_json = {
        "collection_name": "VISITA_CONTROLLO_ECG",
        "operation_type": "aggregate",
        "arguments": {
            "pipeline": [
                {
                    "$lookup": {
                        "from": "ESAMI_LABORATORIO",
                        "localField": "ID_PAZ",
                        "foreignField": "ID_PAZ",
                        "as": "esami_lab"
                    }
                },
                {
                    "$unwind": {
                        "path": "$esami_lab",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id": "$SEZIONE",
                        "max_bmi_value": { "$max": "$BMI" },
                        "min_gfr_value": { "$min": "$esami_lab.FILTRATO_GFR" },
                        "all_patients_in_section": {
                            "$push": {
                                "ID_PAZ": "$ID_PAZ",
                                "BMI": "$BMI",
                                "FILTRATO_GFR": "$esami_lab.FILTRATO_GFR"
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "SEZIONE": "$_id",
                        "max_bmi": "$max_bmi_value",
                        "min_gfr": "$min_gfr_value",
                        "id_paz_max_bmi": {
                            "$filter": {
                                "input": "$all_patients_in_section",
                                "as": "patient",
                                "cond": { "$eq": ["$$patient.BMI", "$max_bmi_value"] }
                            }
                        },
                        "id_paz_min_gfr": {
                            "$filter": {
                                "input": "$all_patients_in_section",
                                "as": "patient",
                                "cond": { "$eq": ["$$patient.FILTRATO_GFR", "$min_gfr_value"] }
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "SEZIONE": 1,
                        "max_bmi": 1,
                        "min_gfr": 1,
                        "id_paz_max_bmi": { "$arrayElemAt": ["$id_paz_max_bmi.ID_PAZ", 0] },
                        "id_paz_min_gfr": { "$arrayElemAt": ["$id_paz_min_gfr.ID_PAZ", 0] }
                    }
                }
            ]
        }
    }


    return gold_json

# Main Function
if __name__ == "__main__":

    query_number_str = input("Insert Number of query to execute: ")
    query_number = int(query_number_str)

    callable_queries = [
        gold_easy_query_n3,
        gold_easy_query_n4,
        gold_easy_query_n5,
        gold_medium_query_n11,
        gold_medium_query_n12,
        gold_medium_query_n13,
        gold_medium_query_n14,
        gold_medium_query_n15
    ]

    if query_number > 0 and query_number <= len(callable_queries):

        gold_json = callable_queries[query_number-1]()
        result_data = executor.execute_query(gold_json)

        df = pd.json_normalize(result_data['data'])
        df.to_csv(os.path.join(results_path, f"results_query_n{query_number}.csv"), index=False)
        print(f"Query executed correctly, results query_n{query_number} saved")


    else:
        print("Not Valid query for this testset")





