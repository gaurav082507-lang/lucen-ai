from typing import Dict, List
from backend.app.explain.llm import generate_llm_summary
from backend.app.explain.templates import render_evidence_reason
from backend.app.schemas.evidence import Evidence


RECOMMENDED_ACTIONS = {
    "LOW": "No significant indicators found. Proceed with standard claim adjudication workflow.",
    "MEDIUM": "Route to manual review. Verify highlighted document fields or image regions before approval.",
    "HIGH": "Escalate to Special Investigation Unit (SIU). Multiple corroborating fraud signals detected.",
}


async def compose_explanation(
    band: str,
    overall_risk: float,
    confidence: str,
    evidence_list: List[Evidence],
    contributions: Dict[str, float],
) -> str:
    """
    Ranks evidence by contribution, formats reasons with templates,
    and constructs the final plain-English investigator summary.
    """
    # Filter to risk evidence and sort by marginal contribution
    risk_evidence = [e for e in evidence_list if e.kind == "risk"]
    sorted_evidence = sorted(
        risk_evidence,
        key=lambda e: contributions.get(e.id, e.effective_weight * e.calibrated_score),
        reverse=True,
    )

    # Re-render reasons through deterministic templates
    for ev in sorted_evidence:
        ev.reason = render_evidence_reason(ev.id, ev.details, ev.reason)

    top_reasons = sorted_evidence[:3]

    # Try LLM summary if configured and valid
    llm_summary = await generate_llm_summary(band, overall_risk, confidence, top_reasons)
    if llm_summary:
        return llm_summary

    # Template fallback
    percent = round(overall_risk * 100)
    lead = f"{band} fraud likelihood ({percent}% overall risk, {confidence} confidence)."

    if not top_reasons:
        return f"{lead} No anomalous patterns or tampering signatures detected. {RECOMMENDED_ACTIONS[band]}"

    reasons_text = " ".join([f"{e.reason}" for e in top_reasons])
    action = RECOMMENDED_ACTIONS.get(band, RECOMMENDED_ACTIONS["LOW"])

    return f"{lead} {reasons_text} Recommendation: {action}"
