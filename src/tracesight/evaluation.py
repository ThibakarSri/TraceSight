"""Evaluator-only functions. Never imported by inference or telemetry adapter."""


def ranking_metrics(ranking: list[str], required_roots: set[str], k: int = 3) -> dict:
    """Any-required-root ranking metrics plus required-root recall at k.

    This is not the complete ops-lite optional/not-effective set scorer.
    """
    if not required_roots or len(ranking) != len(set(ranking)) or k < 1:
        raise ValueError("Nonempty roots, unique ranking, positive k required")
    ranks = [i + 1 for i, service in enumerate(ranking) if service in required_roots]
    return {
        "top1_any_required": bool(ranks and ranks[0] == 1),
        "topk_any_required": bool(ranks and ranks[0] <= k),
        "reciprocal_rank": 1 / ranks[0] if ranks else 0.0,
        "required_recall_at_k": len(set(ranking[:k]) & required_roots) / len(required_roots),
    }
