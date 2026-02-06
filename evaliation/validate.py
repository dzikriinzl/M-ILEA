def calculate_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0 else 0
    )
    return precision, recall, f1


def validate(predictions, ground_truth):
    tp, fp, fn = 0, 0, 0

    gt_types = {p["type"] for p in ground_truth["protections"]}
    pred_types = {p.pattern_type for p in predictions}

    for p in pred_types:
        if p in gt_types:
            tp += 1
        else:
            fp += 1

    for g in gt_types:
        if g not in pred_types:
            fn += 1

    precision, recall, f1 = calculate_metrics(tp, fp, fn)

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Precision": round(precision, 2),
        "Recall": round(recall, 2),
        "F1": round(f1, 2)
    }
