import os
import config  
from pymongo import MongoClient
from query_executor import MongoDBQueryExecutor
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


def gold_easy_query_n1() -> Dict[str, Any]:
    """
    Returns the Gold json for a test query

    Numer of query: N1
    Difficulty: Easy
    User Need: Mi dici dove è nato e quando è nato 
    il paziente con questo codice fiscale GLNGNR56D21F839J
    """

    gold_json = {
        "collection_name": "ANAGRAFICA",
        "operation_type": "find",
        "arguments": {
            "filter": {
                "CODICE_FISCALE": "GLNGNR56D21F839J"    
            },
            "projection": {
                "COMUNE_DI_NASCITA": 1,
                "DATADINASCITA": 1,
                "_id": 0    
            }    
        }    
    }

    return gold_json



# Main Function
if __name__ == "__main__":

    query_number_str = input("Insert Number of query to execute: ")
    query_number = int(query_number_str)
    
    callable_queries = [
        gold_easy_query_n1    
    ]

    if query_number > 0 and query_number <= len(callable_queries):
        
        gold_json = callable_queries[query_number-1]()
        result_data = executor.execute_query(gold_json)

        df = pd.json_normalize(result_data['data'])
        df.to_csv(os.path.join(results_path, f"results_query_n{query_number}.csv"), index=False)
        

    else:
        print("Not Valid query for this testset")


    


