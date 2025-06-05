import pandas as pd
import os

def load_csv_and_get_data_concat(csv_path, id_column, avg_columns=None, precision_decimals=4):
    """
    Carica un CSV, crea una colonna concatenata di ID e valori aggregati,
    e restituisce un set di queste chiavi concatenate.
    Args:
        csv_path (str): Percorso del file CSV.
        id_column (str): Nome della colonna ID_PAZ.
        avg_columns (list): Lista dei nomi delle colonne con valori medi (es. ['avg_bmi', 'avg_gfr']).
        precision_decimals (int): Numero di decimali per arrotondare i valori numerici prima di concatenare.
    Returns:
        set: Un set di stringhe concatenate (ID_PAZ_avg_bmi_avg_gfr), o None in caso di errore.
    """
    try:
        df = pd.read_csv(csv_path.strip(), dtype=str)

        if df.empty:
            print(f"No data found in {csv_path}")
            return set()

        if id_column not in df.columns:
            print(f"Column '{id_column}' not found in {csv_path}")
            return set()

        # Prepara i valori numerici per la concatenazione
        concatenated_keys = set()
        for index, row in df.iterrows():
            id_value = str(row[id_column]).strip()
            
            # Costruisce la parte dei valori medi della chiave concatenata
            avg_parts = []
            if avg_columns:
                for col in avg_columns:
                    if col in df.columns:
                        # Converti in numerico, arrotonda e poi converti in stringa. Gestisci NaN.
                        val = pd.to_numeric(row[col], errors='coerce')
                        if pd.isna(val):
                            avg_parts.append("N/A") # Rappresentazione per valori mancanti
                        else:
                            avg_parts.append(f"{val:.{precision_decimals}f}") # Formatta con decimali
                    else:
                        avg_parts.append("COL_MISSING") # Se la colonna non esiste nel CSV
            
            # Concatena tutte le parti
            composite_key = f"{id_value}_" + "_".join(avg_parts)
            concatenated_keys.add(composite_key)

        print(f"Loaded {len(concatenated_keys)} composite keys from {csv_path}")
        # print(concatenated_keys) # Uncomment for debugging
        return concatenated_keys

    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return None
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None

def load_csv_and_get_ids(csv_path, id_column):

    try:
        df = pd.read_csv(csv_path, dtype=str)

        if df.empty:
            print(f"No data found in {csv_path}")
            return set()

        if id_column not in df.columns:
            print(f"Column '{id_column}' not found in {csv_path}")
            return set()

        identifiers = set(df[id_column].dropna().astype(str))
        print(identifiers)
        return identifiers

    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return None


def calculate_metrics(gold_ids, results_ids):
    TP = len(gold_ids.intersection(results_ids))
    FP = len(results_ids - gold_ids)
    FN = len(gold_ids - results_ids)

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    jaccard_index = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0

    return{
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1_score,
        "Jaccard Index": jaccard_index,
        "TP": TP,
        "FP": FP,
        "FN": FN
    }


if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))

    gold_csv_path = os.path.join(script_dir, "gold_results", "results_query_n20.csv")
    results_rag_csv_path = os.path.join(script_dir, "rag_results", "risultati_query_20.csv")
    results_no_rag_csv_path = os.path.join(script_dir, "wrag_results", "risultati_query_wr_20.csv")


    id_column = "ID_PAZ"

    gold_ids = load_csv_and_get_ids(gold_csv_path, id_column)
    results_rag_ids = load_csv_and_get_ids(results_rag_csv_path, id_column)
    results_no_rag_ids = load_csv_and_get_ids(results_no_rag_csv_path, id_column)

    metrics_rag = calculate_metrics(gold_ids, results_rag_ids)
    metrics_no_rag = calculate_metrics(gold_ids, results_no_rag_ids)

    print("\nMetrics for RAG Results:")
    print("-------------------------")
    for metric, value in metrics_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")

    print("\nMetrics for Non-RAG Results:")
    print("-------------------------")
    for metric, value in metrics_no_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")