from collections import defaultdict
from typing import Dict, List, Tuple
from backend.app.schemas.evidence import Evidence


def fuse_pipeline_evidence(evidence_list: List[Evidence]) -> Tuple[float, Dict[str, float]]:
    """
    Computes pipeline risk using Noisy-OR fusion:
        risk = 1 - PROD(1 - w_i * p_i)

    Applies:
    1. Participation threshold: calibrated_score >= 0.2 AND w_i * p_i >= 0.02
    2. Source cap: combined term of any single detector source capped at 0.40
    3. Contribution attribution: normalized marginal contribution per evidence ID
    """
    risk_evidence = [e for e in evidence_list if e.kind == "risk"]
    if not risk_evidence:
        return 0.0, {}

    # Group terms by source to enforce source cap
    source_terms = defaultdict(list)
    participating_evidence: List[Tuple[Evidence, float]] = []

    for ev in risk_evidence:
        p_i = ev.calibrated_score
        w_i = ev.effective_weight
        term = round(w_i * p_i, 4)

        if p_i >= 0.20 and term >= 0.02:
            source_terms[ev.source].append((ev, term))

    # Apply per-source cap (max 0.40 per source category, e.g. metadata)
    final_terms: List[Tuple[Evidence, float]] = []
    for source, items in source_terms.items():
        total_source_term = sum(t for _, t in items)
        if total_source_term > 0.40 and source in ("metadata", "exif", "pdf_meta"):
            scale = 0.40 / total_source_term
            for ev, t in items:
                final_terms.append((ev, t * scale))
        else:
            final_terms.extend(items)

    if not final_terms:
        return 0.0, {}

    # Calculate Noisy-OR
    prod = 1.0
    for _, t in final_terms:
        prod *= (1.0 - min(t, 0.999))

    raw_risk = 1.0 - prod
    fused_risk = max(0.0, min(1.0, round(raw_risk, 4)))

    # Compute marginal contributions: contribution_i = term_i * PROD_{j != i} (1 - term_j)
    raw_contributions = {}
    n = len(final_terms)
    for i in range(n):
        ev_i, t_i = final_terms[i]
        other_prod = 1.0
        for j in range(n):
            if i != j:
                other_prod *= (1.0 - min(final_terms[j][1], 0.999))
        raw_contributions[ev_i.id] = t_i * other_prod

    # Normalize contributions so they sum exactly to fused_risk
    sum_contrib = sum(raw_contributions.values())
    contributions = {}
    if sum_contrib > 0:
        for ev_id, c in raw_contributions.items():
            contributions[ev_id] = round((c / sum_contrib) * fused_risk, 4)
    else:
        for ev_i, _ in final_terms:
            contributions[ev_i.id] = 0.0

    return fused_risk, contributions


def blend_overall_risk(pipeline_risks: Dict[str, float]) -> float:
    """
    Blends multiple active pipeline risks:
        overall = 0.7 * max(R_k) + 0.3 * mean(R_k)
    If only one pipeline ran, returns that pipeline's risk.
    """
    valid_risks = [r for r in pipeline_risks.values() if r is not None]
    if not valid_risks:
        return 0.0
    if len(valid_risks) == 1:
        return round(valid_risks[0], 4)

    max_risk = max(valid_risks)
    mean_risk = sum(valid_risks) / len(valid_risks)
    overall = (0.7 * max_risk) + (0.3 * mean_risk)
    return max(0.0, min(1.0, round(overall, 4)))
