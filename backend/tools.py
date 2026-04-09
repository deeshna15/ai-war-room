from backend.data import load_metrics, load_feedback, load_release_notes

def get_metric_trend(metric_name: str) -> str:
    metrics = load_metrics()
    if metric_name == "all":
        return str(metrics)
    return str({k: v for k, v in metrics.items() if metric_name in k})

def analyze_sentiment(filter_by_keyword: str = "") -> str:
    feedback = load_feedback()
    if filter_by_keyword:
        return str([f for f in feedback if filter_by_keyword.lower() in str(f.get('comment', '')).lower()])
    return str(feedback)

def get_release_notes() -> str:
    return load_release_notes()
