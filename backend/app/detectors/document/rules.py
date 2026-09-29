from datetime import datetime
from typing import Any, Dict, List
from backend.app.schemas.evidence import Evidence


class DocumentRulesDetector:
    name: str = "consistency_rules"
    timeout_s: float = 4.0

    def run_checks(self, fields: Dict[str, Any], spans: List[Dict[str, Any]]) -> List[Evidence]:
        evidence: List[Evidence] = []
        currency = fields.get("currency", "INR")

        # 1. DOC-LOGIC-01: Line items sum != total
        total_info = fields.get("total")
        line_items = fields.get("line_items", [])
        tax_info = fields.get("tax")

        if total_info and len(line_items) >= 2:
            items_sum = sum(item["value"] for item in line_items)
            stated_total = total_info["value"]
            tax_val = tax_info["value"] if tax_info else 0.0

            # Allow for optional tax addition
            matches_exact = abs(items_sum - stated_total) < 0.05
            matches_with_tax = abs((items_sum + tax_val) - stated_total) < 0.05

            if not matches_exact and not matches_with_tax:
                discrepancy = abs(stated_total - items_sum)
                evidence.append(
                    Evidence(
                        id="DOC-LOGIC-01",
                        pipeline="document",
                        source="consistency_rules",
                        kind="risk",
                        raw_score=1.0,
                        calibrated_score=1.0,
                        weight=0.80,
                        effective_weight=0.80,
                        severity="high",
                        title="Line Items Sum Mismatch",
                        reason=f"Line items sum to {items_sum:,.2f} {currency}, but the stated invoice total is {stated_total:,.2f} {currency}.",
                        field="total_amount",
                        bbox=total_info["bbox"],
                        details={
                            "expected": round(items_sum, 2),
                            "found": round(stated_total, 2),
                            "discrepancy": round(discrepancy, 2),
                            "currency": currency,
                        },
                    )
                )

        # 2. DOC-LOGIC-03: Chronological Date Violations
        date_info = fields.get("date")
        due_info = fields.get("due_date")
        if date_info and due_info:
            try:
                # Try common formats
                def parse_date(s):
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                        try:
                            return datetime.strptime(s, fmt)
                        except ValueError:
                            pass
                    return None

                d_inv = parse_date(date_info["value"])
                d_due = parse_date(due_info["value"])
                if d_inv and d_due and d_due < d_inv:
                    evidence.append(
                        Evidence(
                            id="DOC-LOGIC-03",
                            pipeline="document",
                            source="consistency_rules",
                            kind="risk",
                            raw_score=0.85,
                            calibrated_score=0.85,
                            weight=0.50,
                            effective_weight=0.50,
                            severity="medium",
                            title="Invalid Date Chronology",
                            reason=f"Payment due date ({due_info['value']}) precedes the invoice issuance date ({date_info['value']}).",
                            field="due_date",
                            bbox=due_info["bbox"],
                            details={"invoice_date": date_info["value"], "due_date": due_info["value"]},
                        )
                    )
            except Exception:
                pass

        # 3. DOC-LOGIC-06: Inconsistent numeric formatting across amounts
        all_amounts = fields.get("all_amounts", [])
        if len(all_amounts) >= 3:
            raw_texts = [item["span"]["text"] for item in all_amounts]
            has_comma_decimal = any("," in t and "." not in t for t in raw_texts)
            has_dot_decimal = any("." in t and "," not in t for t in raw_texts)
            if has_comma_decimal and has_dot_decimal:
                evidence.append(
                    Evidence(
                        id="DOC-LOGIC-06",
                        pipeline="document",
                        source="consistency_rules",
                        kind="risk",
                        raw_score=0.60,
                        calibrated_score=0.60,
                        weight=0.25,
                        effective_weight=0.25,
                        severity="low",
                        title="Mixed Numeric Formatting",
                        reason="Document mixes European and standard decimal separator notations within the same table.",
                        details={"sample_formats": raw_texts[:4]},
                    )
                )

        return evidence
