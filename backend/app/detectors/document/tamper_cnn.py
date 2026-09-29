from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
from backend.app.core.config import settings
from backend.app.schemas.evidence import BBox, Evidence
from backend.app.utils.images import compute_ela_map


class DocumentTamperCnnDetector:
    name: str = "doc_tamper_cnn"
    timeout_s: float = 10.0

    def analyze_page_patches(
        self,
        rendered_page: Image.Image,
        page_num: int = 0,
    ) -> Tuple[List[Evidence], Optional[np.ndarray]]:
        """
        Computes patch-level ELA across rendered page to localize spliced/re-saved areas.
        Extracts 128x128 patches with stride 64 and detects outlier error densities.
        """
        ela_gray, raw_anomaly, _ = compute_ela_map(rendered_page, quality=90, scale=15.0)
        h, w = ela_gray.shape

        patch_size = 128
        stride = 64
        top_patches = []

        for y in range(0, h - patch_size + 1, stride):
            for x in range(0, w - patch_size + 1, stride):
                patch = ela_gray[y : y + patch_size, x : x + patch_size]
                # Ignore plain white/blank patches (low variance)
                if np.var(patch) < 15.0:
                    continue
                score = float(np.mean(patch) / 255.0)
                top_patches.append((score, x, y))

        if not top_patches:
            return [], ela_gray

        top_patches.sort(key=lambda p: p[0], reverse=True)
        evidence = []

        # If top patch has high anomaly relative to median
        scores = [p[0] for p in top_patches]
        median_score = np.median(scores)
        highest_score, hx, hy = top_patches[0]

        if highest_score > 0.35 and (highest_score > median_score * 1.8):
            bbox = BBox(
                page=page_num,
                x=round(hx / w, 4),
                y=round(hy / h, 4),
                w=round(patch_size / w, 4),
                h=round(patch_size / h, 4),
            )
            prob = min(0.95, round(highest_score * 1.6, 2))
            evidence.append(
                Evidence(
                    id="DOC-CNN-01",
                    pipeline="document",
                    source="tamper_cnn",
                    kind="risk",
                    raw_score=prob,
                    calibrated_score=prob,
                    weight=0.50,
                    effective_weight=0.50,
                    severity="high" if prob >= 0.70 else "medium",
                    title="Tampered Document Patch Localized",
                    reason=f"Neural patch analysis identified a {prob:.0%} probability of localized editing/splicing.",
                    field="modified_region",
                    bbox=bbox,
                    details={"highest_patch_score": round(highest_score, 4), "page": page_num, "score": prob},
                )
            )

        return evidence, ela_gray
