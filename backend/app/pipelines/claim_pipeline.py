from datetime import datetime
from typing import Any, Dict, List
from rapidfuzz import fuzz
from backend.app.detectors.base import AnalysisContext
from backend.app.schemas.evidence import Evidence


class ClaimCrossCheckDetector:
    name: str = "cross_checks"
    timeout_s: float = 3.0

    def run_cross_checks(self, ctx: AnalysisContext) -> List[Evidence]:
        evidence: List[Evidence] = []
        meta = ctx.claim_metadata
        if not meta:
            return evidence

        doc_fields = ctx.extras.get("document_fields", {})
        exif = ctx.extras.get("exif", {})

        # 1. CLM-X-02: Amount in document != Claimed Amount
        total_info = doc_fields.get("total")
        if total_info and meta.claimed_amount is not None:
            doc_total = total_info["value"]
            claimed = meta.claimed_amount
            discrepancy = abs(doc_total - claimed)
            if discrepancy > 1.0: # Discrepancy greater than 1 unit
                evidence.append(
                    Evidence(
                        id="CLM-X-02",
                        pipeline="claim",
                        source="cross_modal",
                        kind="risk",
                        raw_score=0.85,
                        calibrated_score=0.85,
                        weight=0.50,
                        effective_weight=0.50,
                        severity="medium",
                        title="Claim Amount Mismatch",
                        reason=f"Declared claim amount ({claimed:,.2f} {meta.currency}) differs from invoice document total ({doc_total:,.2f} {meta.currency}).",
                        field="claimed_amount",
                        bbox=total_info.get("bbox"),
                        details={
                            "doc_total": doc_total,
                            "claim_total": claimed,
                            "discrepancy": round(discrepancy, 2),
                            "currency": meta.currency,
                        },
                    )
                )

        # 2. CLM-X-01: Incident date vs Photo capture date
        photo_date_raw = exif.get("DateTimeOriginal")
        if photo_date_raw and meta.incident_date:
            try:
                # Format: 2026:09:10 14:30:00 vs 2026-09-10
                p_date_str = str(photo_date_raw)[:10].replace(":", "-")
                d_photo = datetime.strptime(p_date_str, "%Y-%m-%d")
                d_incident = datetime.strptime(meta.incident_date, "%Y-%m-%d")
                days_diff = abs((d_photo - d_incident).days)
                if days_diff > 3:
                    evidence.append(
                        Evidence(
                            id="CLM-X-01",
                            pipeline="claim",
                            source="cross_modal",
                            kind="risk",
                            raw_score=0.70,
                            calibrated_score=0.70,
                            weight=0.40,
                            effective_weight=0.40,
                            severity="medium",
                            title="Photo Timestamp Discrepancy",
                            reason=f"Photo EXIF capture date ({p_date_str}) is {days_diff} days divergent from stated incident date ({meta.incident_date}).",
                            details={"photo_date": p_date_str, "incident_date": meta.incident_date, "days_diff": days_diff},
                        )
                    )
            except Exception:
                pass

        # 3. CLM-X-03: Claimant name cross-check
        if meta.claimant_name and doc_fields.get("claimant_name"):
            name_doc = doc_fields["claimant_name"]
            sim_ratio = fuzz.token_sort_ratio(meta.claimant_name.lower(), name_doc.lower())
            if sim_ratio < 70:
                evidence.append(
                    Evidence(
                        id="CLM-X-03",
                        pipeline="claim",
                        source="cross_modal",
                        kind="risk",
                        raw_score=0.80,
                        calibrated_score=0.80,
                        weight=0.45,
                        effective_weight=0.45,
                        severity="medium",
                        title="Claimant Name Mismatch",
                        reason=f"Claimant name '{meta.claimant_name}' does not match document party name '{name_doc}'.",
                        details={"claimant_name": meta.claimant_name, "doc_name": name_doc, "match_ratio": sim_ratio},
                    )
                )

        return evidence
