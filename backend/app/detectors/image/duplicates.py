from pathlib import Path
from PIL import Image
import imagehash
from backend.app.db.repository import find_duplicate_hashes, save_image_hash
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence


class ImageDuplicateDetector:
    name: str = "duplicates"
    timeout_s: float = 4.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        img = ctx.extras.get("decoded_image") or Image.open(img_path).convert("RGB")
        phash_val = str(imagehash.phash(img))
        ctx.extras["phash"] = phash_val

        evidence = []
        matches = find_duplicate_hashes(phash_val, max_hamming_distance=6)

        if matches:
            matched_id, dist = matches[0]
            dist_int = int(dist)
            similarity = float(round(1.0 - (dist_int / 64.0), 2))
            evidence.append(
                Evidence(
                    id="IMG-DUP-01",
                    pipeline="image",
                    source="duplicates",
                    kind="risk",
                    raw_score=similarity,
                    calibrated_score=similarity,
                    weight=0.70,
                    effective_weight=0.70,
                    severity="high" if similarity >= 0.90 else "medium",
                    title="Duplicate Claim Photo Detected",
                    reason=f"Photo closely matches an image previously submitted in claim '{matched_id}' ({similarity:.0%} match).",
                    details={"other_id": str(matched_id), "hamming_distance": dist_int, "similarity": similarity},
                )
            )

        safe_matches = [(str(m[0]), int(m[1])) for m in matches]
        return DetectorOutput(evidence=evidence, extras={"phash": phash_val, "duplicate_matches": safe_matches})
