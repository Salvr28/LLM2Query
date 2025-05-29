import pandas as pd


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
    gold_csv_path = "risultati_query_20250522_102519.csv "
    results_rag_csv_path = "risultati_query_20250522_104526.csv"
    results_no_rag_csv_path = "risultati_query_20250522_104526.csv"

    id_column = "CODPAZ"

    gold_ids = load_csv_and_get_ids(gold_csv_path, id_column)
    results_rag_ids = load_csv_and_get_ids(results_rag_csv_path, id_column)
    results_no_rag_ids = load_csv_and_get_ids(results_no_rag_csv_path, id_column)

    metrics_rag = calculate_metrics(gold_ids, results_rag_ids)
    metrics_no_rag = calculate_metrics(gold_ids, results_no_rag_ids)

    for metric, value in metrics_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")

    for metric, value in metrics_no_rag.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")