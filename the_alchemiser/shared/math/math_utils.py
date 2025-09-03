"""Business Unit: shared | Status: current..

    Args:
        performance_metrics (list): List of performance values
        weights (list, optional): Weights for each metric. If None, equal weights are used

    Returns:
        float: Weighted ensemble score

    """
    if not performance_metrics:
        return 0.0

    metrics = [float(m) for m in performance_metrics if not pd.isna(m)]
    if not metrics:
        return 0.0

    if weights is None:
        weights = [1.0] * len(metrics)
    else:
        weights = weights[: len(metrics)]  # Truncate if too long
        if len(weights) < len(metrics):
            weights.extend([1.0] * (len(metrics) - len(weights)))  # Pad if too short

    try:
        weighted_sum = sum(m * w for m, w in zip(metrics, weights, strict=False))
        total_weight = sum(weights)
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    except Exception:
        return 0.0
