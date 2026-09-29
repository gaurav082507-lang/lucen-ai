from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image
from backend.app.core.config import settings
from backend.app.detectors.base import AnalysisContext, run_safely
from backend.app.detectors.image.ai_detector import ImageAiDetector
from backend.app.detectors.image.duplicates import ImageDuplicateDetector
from backend.app.detectors.image.ela import ImageElaDetector
from backend.app.detectors.image.metadata import ImageMetadataDetector
from backend.app.detectors.image.noise import ImageNoiseDetector
from backend.app.detectors.image.preprocess import ImagePreprocessDetector
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.result import DetectorStatus
from backend.app.utils.images import save_forensic_heatmap


class ImagePipeline:
    def __init__(self):
        self.preprocess_detector = ImagePreprocessDetector()
        self.metadata_detector = ImageMetadataDetector()
        self.ai_detector = ImageAiDetector()
        self.ela_detector = ImageElaDetector()
        self.noise_detector = ImageNoiseDetector()
        self.dup_detector = ImageDuplicateDetector()

    def run(
        self,
        ctx: AnalysisContext,
        result_id: str,
        progress_cb=None,
    ) -> Tuple[List[Evidence], List[DetectorStatus], Dict[str, str]]:
        all_evidence: List[Evidence] = []
        statuses: List[DetectorStatus] = []
        artifacts: Dict[str, str] = {}

        detectors = [
            ("preprocess", self.preprocess_detector),
            ("metadata", self.metadata_detector),
            ("ai_detector", self.ai_detector),
            ("ela", self.ela_detector),
            ("noise", self.noise_detector),
            ("duplicates", self.dup_detector),
        ]

        for step_name, det in detectors:
            if progress_cb:
                progress_cb(step_name, "running")
            output, status = run_safely(det, ctx)
            statuses.append(status)
            all_evidence.extend(output.evidence)
            if progress_cb:
                progress_cb(step_name, "done" if status.status == "ok" else status.status)

        # Generate Heatmap Artifact
        img = ctx.extras.get("decoded_image")
        ela_map = ctx.extras.get("ela_map")
        noise_map = ctx.extras.get("noise_map")

        if img is not None:
            w, h = img.size
            if ela_map is None:
                ela_map = np.zeros((h, w), dtype=np.uint8)
            if noise_map is None:
                noise_map = np.zeros((h, w), dtype=np.uint8)

            heatmap_filename = f"image_heatmap.png"
            heatmap_path = settings.ARTIFACTS_DIR / result_id / heatmap_filename
            save_forensic_heatmap(img, ela_map, noise_map, heatmap_path)
            artifacts["image_heatmap"] = f"{settings.API_V1_STR}/artifacts/{result_id}/{heatmap_filename}"

        return all_evidence, statuses, artifacts
