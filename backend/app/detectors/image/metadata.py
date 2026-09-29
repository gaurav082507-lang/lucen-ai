from datetime import datetime
from pathlib import Path
from PIL import ExifTags, Image
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence


AI_GENERATOR_KEYWORDS = [
    "midjourney", "stable diffusion", "dall-e", "dalle", "firefly", "comfyui",
    "automatic1111", "novelai", "invokeai", "bing image creator", "flux.1", "imagen"
]

IMAGE_EDITOR_KEYWORDS = [
    "adobe photoshop", "photoshop", "gimp", "lightroom", "snapseed", "canva",
    "affinity photo", "pixelmator", "paint.net", "facetune", "picsart"
]


class ImageMetadataDetector:
    name: str = "image_metadata"
    timeout_s: float = 5.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        img = ctx.extras.get("decoded_image") or Image.open(img_path)
        exif_data = {}
        try:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="ignore")
                        except Exception:
                            value = str(value)
                    exif_data[tag_name] = value
        except Exception:
            pass

        evidence = []

        # 1. Missing camera EXIF
        has_camera_make = bool(exif_data.get("Make") or exif_data.get("Model"))
        if not has_camera_make:
            evidence.append(
                Evidence(
                    id="IMG-EXIF-01",
                    pipeline="image",
                    source="exif",
                    kind="risk",
                    raw_score=0.50,
                    calibrated_score=0.50,
                    weight=0.10,
                    effective_weight=0.10,
                    severity="low",
                    title="No Camera EXIF Present",
                    reason="Image contains no camera hardware metadata (common when shared through messaging apps).",
                    details={"exif_keys_present": list(exif_data.keys())},
                )
            )

        # 2. Software tag analysis
        software_field = str(exif_data.get("Software", "")).lower()
        artist_field = str(exif_data.get("Artist", "")).lower()
        combined_text = f"{software_field} {artist_field}"

        found_gen = next((kw for kw in AI_GENERATOR_KEYWORDS if kw in combined_text), None)
        if found_gen:
            evidence.append(
                Evidence(
                    id="IMG-EXIF-02a",
                    pipeline="image",
                    source="exif",
                    kind="risk",
                    raw_score=0.95,
                    calibrated_score=0.95,
                    weight=0.80,
                    effective_weight=0.80,
                    severity="high",
                    title="AI Image Generator Tag Detected",
                    reason=f"File metadata explicitly specifies generative AI tool: '{found_gen}'.",
                    details={"software": exif_data.get("Software", found_gen)},
                )
            )

        found_edit = next((kw for kw in IMAGE_EDITOR_KEYWORDS if kw in combined_text), None)
        if found_edit and not found_gen:
            evidence.append(
                Evidence(
                    id="IMG-EXIF-02b",
                    pipeline="image",
                    source="exif",
                    kind="risk",
                    raw_score=0.75,
                    calibrated_score=0.75,
                    weight=0.35,
                    effective_weight=0.35,
                    severity="medium",
                    title="Image Editing Software Detected",
                    reason=f"File metadata indicates image manipulation tool: '{found_edit}'.",
                    details={"software": exif_data.get("Software", found_edit)},
                )
            )

        # 3. Timestamp consistency
        dt_orig = exif_data.get("DateTimeOriginal")
        dt_mod = exif_data.get("DateTime")
        if dt_orig and dt_mod:
            try:
                fmt = "%Y:%m:%d %H:%M:%S"
                t_orig = datetime.strptime(str(dt_orig)[:19], fmt)
                t_mod = datetime.strptime(str(dt_mod)[:19], fmt)
                if t_orig > t_mod:
                    evidence.append(
                        Evidence(
                            id="IMG-EXIF-03",
                            pipeline="image",
                            source="exif",
                            kind="risk",
                            raw_score=0.70,
                            calibrated_score=0.70,
                            weight=0.30,
                            effective_weight=0.30,
                            severity="medium",
                            title="Inconsistent EXIF Timestamps",
                            reason=f"Original capture date ({dt_orig}) post-dates modification date ({dt_mod}).",
                            details={"capture": str(dt_orig), "modify": str(dt_mod)},
                        )
                    )
            except Exception:
                pass

        return DetectorOutput(evidence=evidence, extras={"exif": exif_data})
