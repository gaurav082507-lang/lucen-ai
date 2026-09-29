from collections import Counter
from typing import Any, Dict, List
from backend.app.schemas.evidence import Evidence


class DocumentFontDetector:
    name: str = "font_consistency"
    timeout_s: float = 4.0

    def check_fonts(self, spans: List[Dict[str, Any]], fields: Dict[str, Any]) -> List[Evidence]:
        evidence: List[Evidence] = []
        all_amounts = fields.get("all_amounts", [])

        # 1. DOC-FONT-01: Font differs within amount column
        if len(all_amounts) >= 3:
            font_counts = Counter(item["span"]["font"] for item in all_amounts)
            dominant_font, dom_count = font_counts.most_common(1)[0]

            for item in all_amounts:
                span_font = item["span"]["font"]
                if span_font != dominant_font and dom_count >= 2:
                    val = item["amount"]
                    evidence.append(
                        Evidence(
                            id="DOC-FONT-01",
                            pipeline="document",
                            source="font_analysis",
                            kind="risk",
                            raw_score=0.75,
                            calibrated_score=0.75,
                            weight=0.40,
                            effective_weight=0.40,
                            severity="medium",
                            title="Font Discrepancy in Stated Amount",
                            reason=f"Amount '{item['span']['text']}' uses font '{span_font}' differing from column font '{dominant_font}'.",
                            field="amount",
                            bbox=item["bbox"],
                            details={"text": item["span"]["text"], "font_a": span_font, "font_b": dominant_font},
                        )
                    )
                    break

        # 2. DOC-FONT-02: Font size outlier in line
        if len(all_amounts) >= 3:
            sizes = [item["span"]["size"] for item in all_amounts]
            median_size = sorted(sizes)[len(sizes) // 2]

            for item in all_amounts:
                size = item["span"]["size"]
                if abs(size - median_size) > 2.5: # Significant size outlier
                    evidence.append(
                        Evidence(
                            id="DOC-FONT-02",
                            pipeline="document",
                            source="font_analysis",
                            kind="risk",
                            raw_score=0.65,
                            calibrated_score=0.65,
                            weight=0.30,
                            effective_weight=0.30,
                            severity="low",
                            title="Anomalous Font Size in Table Line",
                            reason=f"Text span '{item['span']['text']}' has size {size}pt, deviating from table median {median_size}pt.",
                            bbox=item["bbox"],
                            details={"text": item["span"]["text"], "size": size, "median_size": median_size},
                        )
                    )
                    break

        return evidence
