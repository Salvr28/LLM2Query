import pandas as pd
import numpy as np

def load_data_for_evaluation(csv_path, id_column, value_columns_to_check):
    """
    Loads data from the CSV, extracting the specified ID and value columns.
    Returns a set of tuples, where each tuple represents a record
    (id, value1, value2, ...). Numeric values are rounded
    and missing values (NaN) are converted into a placeholder string 'MISSING'.
    """
    try:
        # Reads ID as string and attempts to convert other columns to numeric
        # Keeps ID as string to avoid problems with numeric formats
        df = pd.read_csv(csv_path, dtype={id_column: str})

        for col in value_columns_to_check:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Warning: Value column '{col}' is not present in {csv_path}. It will be treated as missing for all records.")
                df[col] = np.nan # Create the column with NaN if it doesn't exist

        if df.empty:
            print(f"No data found in {csv_path}")
            return set()

        if id_column not in df.columns:
            print(f"ID column '{id_column}' not found in {csv_path}")
            return set() # Returns an empty set if the ID column is not present

        records = set()
        for _, row in df.iterrows():
            identifier = row[id_column]

            # Skip rows if the main identifier is missing
            if pd.isna(identifier) or str(identifier).strip() == "":
                continue

            current_record_values = [identifier]
            for col in value_columns_to_check:
                value = row[col]
                if pd.isna(value):
                    current_record_values.append("MISSING")
                elif isinstance(value, float):
                    current_record_values.append(round(value, 4))
                else: # Integers or other types converted from to_numeric
                    current_record_values.append(value)

            records.add(tuple(current_record_values))

        return records

    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return None
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
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
    # Uncomment the following line if you want to check specific value columns
    #value_columns_to_check = ['uomini', 'donne']

    gold_ids = load_csv_and_get_ids(gold_csv_path, id_column)
    results_rag_ids = load_csv_and_get_ids(results_rag_csv_path, id_column)
    results_no_rag_ids = load_csv_and_get_ids(results_no_rag_csv_path, id_column)

    # If you want to check specific value columns, uncomment the following lines
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