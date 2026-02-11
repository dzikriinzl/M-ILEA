import json
from pathlib import Path

def calculate_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0)
    return precision, recall, f1

def validate_results(predictions_json, ground_truth_json):
    """
    predictions_json: data dari report.json
    ground_truth_json: data dari evaluation/ground_truth/app.json
    """
    tp, fp, fn = 0, 0, 0

    # Gunakan kombinasi Class + Method sebagai identifier unik
    gt_locations = {f"{p['location']['class']}->{p['location']['method']}" 
                    for p in ground_truth_json["protections"]}
    
    pred_locations = {f"{p['location']['class']}->{p['location']['method']}" 
                      for p in predictions_json["findings"]}

    # Hitung True Positive & False Positive
    for loc in pred_locations:
        if loc in gt_locations:
            tp += 1
        else:
            fp += 1

    # Hitung False Negative (yang terlewat oleh M-ILEA)
    for loc in gt_locations:
        if loc not in pred_locations:
            fn += 1

    p, r, f1 = calculate_metrics(tp, fp, fn)

    return {
        "metrics": {"precision": p, "recall": r, "f1": f1},
        "counts": {"tp": tp, "fp": fp, "fn": fn}
    }

if __name__ == "__main__":
    # Contoh pemanggilan untuk pengujian
    # with open("report.json") as f1, open("evaluation/ground_truth/app1.json") as f2:
    #     print(validate_results(json.load(f1), json.load(f2)))
    pass