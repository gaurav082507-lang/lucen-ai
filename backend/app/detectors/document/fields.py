import re
from typing import Any, Dict, List, Optional
from backend.app.schemas.evidence import BBox


def parse_numeric_amount(text: str) -> Optional[float]:
    clean = re.sub(r"[^\d.,]", "", text).strip()
    if not clean:
        return None
    # Handle European vs US number formatting (e.g. 1.250,50 vs 1,250.50)
    if "," in clean and "." in clean:
        if clean.rfind(",") > clean.rfind("."):
            clean = clean.replace(".", "").replace(",", ".")
        else:
            clean = clean.replace(",", "")
    elif "," in clean:
        # Check if comma is decimal or thousand separator
        parts = clean.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            clean = clean.replace(",", ".")
        else:
            clean = clean.replace(",", "")
    try:
        return float(clean)
    except ValueError:
        return None


def extract_document_fields(spans: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts structured fields (totals, line items, dates, policy IDs)
    and maps them to their respective text spans and bounding boxes.
    """
    fields: Dict[str, Any] = {
        "invoice_number": None,
        "policy_number": None,
        "date": None,
        "due_date": None,
        "total": None,
        "subtotal": None,
        "tax": None,
        "currency": "INR",
        "line_items": [],
        "all_amounts": [],
        "claimant_name": None,
    }

    # First pass: find full document text and scan for currency
    full_text = " ".join([s["text"] for s in spans])
    if "$" in full_text or "USD" in full_text:
        fields["currency"] = "USD"
    elif "€" in full_text or "EUR" in full_text:
        fields["currency"] = "EUR"
    elif "£" in full_text or "GBP" in full_text:
        fields["currency"] = "GBP"

    # Regex patterns
    date_regex = re.compile(r"\b(?:\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})\b")
    amount_regex = re.compile(r"(?:[$€£₹]|rs\.?|inr)?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\b", re.IGNORECASE)

    for i, span in enumerate(spans):
        text = span["text"].strip()
        lower = text.lower()

        # Invoice / Policy number
        if "invoice" in lower and ("#" in lower or "no" in lower or "num" in lower):
            match = re.search(r"[A-Z0-9-]{4,}", text)
            if match and not fields["invoice_number"]:
                fields["invoice_number"] = {"value": match.group(0), "span": span, "bbox": span["bbox_norm"]}
        elif "policy" in lower and ("#" in lower or "no" in lower or "num" in lower):
            match = re.search(r"[A-Z0-9-]{5,}", text)
            if match and not fields["policy_number"]:
                fields["policy_number"] = {"value": match.group(0), "span": span, "bbox": span["bbox_norm"]}

        # Dates
        date_match = date_regex.search(text)
        if date_match:
            d_val = date_match.group(0)
            if ("due" in lower or (i > 0 and "due" in spans[i - 1]["text"].lower())) and not fields["due_date"]:
                fields["due_date"] = {"value": d_val, "span": span, "bbox": span["bbox_norm"]}
            elif not fields["date"]:
                fields["date"] = {"value": d_val, "span": span, "bbox": span["bbox_norm"]}

        # Totals and Subtotals
        amt_match = amount_regex.search(text)
        if amt_match:
            num = parse_numeric_amount(amt_match.group(1))
            if num is not None:
                fields["all_amounts"].append({"amount": num, "span": span, "bbox": span["bbox_norm"]})
                # Check preceding span context or current text
                prev_text = spans[i - 1]["text"].lower() if i > 0 else ""
                combined = f"{prev_text} {lower}"

                if "total" in combined and "sub" not in combined:
                    if not fields["total"] or num > fields["total"]["value"]:
                        fields["total"] = {"value": num, "span": span, "bbox": span["bbox_norm"]}
                elif "subtotal" in combined or "sub-total" in combined:
                    fields["subtotal"] = {"value": num, "span": span, "bbox": span["bbox_norm"]}
                elif "tax" in combined or "gst" in combined or "vat" in combined:
                    fields["tax"] = {"value": num, "span": span, "bbox": span["bbox_norm"]}
                elif "amount" in combined or "cost" in combined or "price" in combined:
                    fields["line_items"].append({"value": num, "span": span, "bbox": span["bbox_norm"]})

    # If line items weren't explicitly categorized, populate from all_amounts except total/subtotal
    if not fields["line_items"] and fields["all_amounts"]:
        total_val = fields["total"]["value"] if fields["total"] else None
        subtotal_val = fields["subtotal"]["value"] if fields["subtotal"] else None
        tax_val = fields["tax"]["value"] if fields["tax"] else None

        for item in fields["all_amounts"]:
            val = item["amount"]
            if val not in [total_val, subtotal_val, tax_val] and val > 0:
                fields["line_items"].append({"value": val, "span": item["span"], "bbox": item["bbox"]})

    return fields
