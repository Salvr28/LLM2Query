import pandas as pd
import numpy as np

def load_data_for_evaluation(csv_path, id_column, value_columns_to_check):
    """
    Carica i dati dal CSV, estraendo l'ID e le colonne dei valori specificate.
    Restituisce un set di tuple, dove ogni tupla rappresenta un record
    (id, valore1, valore2, ...). I valori numerici vengono arrotondati
    e i valori mancanti (NaN) vengono convertiti in una stringa placeholder "MISSING".
    """
    try:
        # Legge l'ID come stringa e tenta di convertire le altre colonne in numerico
        # Mantiene l'ID come stringa per evitare problemi con formati numerici
        df = pd.read_csv(csv_path, dtype={id_column: str})

        for col in value_columns_to_check:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Attenzione: La colonna valore '{col}' non è presente in {csv_path}. Sarà trattata come mancante per tutti i record.")
                df[col] = np.nan # Crea la colonna con NaN se non esiste

        if df.empty:
            print(f"Nessun dato trovato in {csv_path}")
            return set()

        if id_column not in df.columns:
            print(f"La colonna ID '{id_column}' non è stata trovata in {csv_path}")
            return set() # Restituisce un set vuoto se la colonna ID non c'è

        records = set()
        for _, row in df.iterrows():
            identifier = row[id_column]

            # Salta le righe se l'identificatore principale è mancante
            if pd.isna(identifier) or str(identifier).strip() == "":
                # print(f"Riga saltata in {csv_path} a causa di ID mancante.")
                continue

            current_record_values = [identifier]
            for col in value_columns_to_check:
                value = row[col]
                if pd.isna(value):
                    current_record_values.append("MISSING")
                elif isinstance(value, float):
                    current_record_values.append(round(value, 4)) # Arrotonda i float a 4 decimali
                else: # Interi o altri tipi convertiti da to_numeric
                    current_record_values.append(value)

            records.add(tuple(current_record_values))

        # print(f"Caricati {len(records)} record unici da {csv_path} per il confronto.")
        return records

    except FileNotFoundError:
        print(f"File non trovato: {csv_path}")
        return None # Importante per la gestione errori nel chiamante
    except Exception as e:
        print(f"Errore durante il caricamento di {csv_path}: {e}")
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
    gold_csv_path = "results_query_n16.csv"
    results_rag_csv_path = "risultati_query_16.csv"
    results_no_rag_csv_path = "risultati_query_wr_16.csv"

    id_column = "total"
    #value_columns_to_check = ['uomini', 'donne']

    gold_ids = load_csv_and_get_ids(gold_csv_path, id_column)
    results_rag_ids = load_csv_and_get_ids(results_rag_csv_path, id_column)
    results_no_rag_ids = load_csv_and_get_ids(results_no_rag_csv_path, id_column)

    #gold_ids = load_data_for_evaluation(gold_csv_path, id_column, value_columns_to_check)
    #results_rag_ids = load_data_for_evaluation(results_rag_csv_path, id_column, value_columns_to_check)
    #results_no_rag_ids = load_data_for_evaluation(results_no_rag_csv_path, id_column, value_columns_to_check)

    metrics_rag = calculate_metrics(gold_ids, results_rag_ids)
    metrics_no_rag = calculate_metrics(gold_ids, results_no_rag_ids)

    print("Metrics for RAG Results:")
    print("-------------------------")
    for metric, value in metrics_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")

    print("Metrics for Non-RAG Results:")
    print("------------------------------")
    for metric, value in metrics_no_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")