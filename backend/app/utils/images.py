import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageOps
from backend.app.schemas.evidence import BBox


def load_and_orient_image(image_path: Path) -> Image.Image:
    """Loads image and corrects EXIF orientation, converted to RGB."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Cap dimensions to 1600px to prevent OOM (Out Of Memory) on 512MB RAM cloud tiers like Render
    max_dim = 1600
    if max(img.width, img.height) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    return img


def compute_image_quality_metrics(image_path: Path, img: Image.Image) -> Dict[str, any]:
    """
    Extracts quality attributes: resolution, sharpness (Laplacian variance),
    estimated JPEG quality, and screenshot indicators.
    """
    w, h = img.size
    short_side = min(w, h)
    megapixels = round((w * h) / 1_000_000, 2)

    # Sharpness via Laplacian variance
    np_img = np.array(img)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # JPEG quality estimation
    is_jpeg = image_path.suffix.lower() in [".jpg", ".jpeg"]
    jpeg_quality = 85
    if is_jpeg:
        try:
            # Inspect quantization tables if present
            quant_tables = getattr(img, "quantization", None)
            if quant_tables and 0 in quant_tables:
                table = quant_tables[0]
                avg_q = sum(table) / len(table)
                # Lower quantization values correspond to higher quality
                jpeg_quality = max(10, min(100, int(100 - (avg_q / 2))))
        except Exception:
            jpeg_quality = 85

    # Check for screenshot characteristics: common screen aspect ratios & flat UI areas
    aspect = max(w, h) / max(1, min(w, h))
    common_screen_ratios = [16 / 9, 16 / 10, 19.5 / 9, 20 / 9, 4 / 3]
    is_screen_ratio = any(abs(aspect - r) < 0.02 for r in common_screen_ratios)

    # Flat region check: ratio of low-gradient pixels
    dx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    dy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    mag = cv2.magnitude(dx, dy)
    flat_ratio = float(np.mean(mag < 3.0))
    is_screenshot = is_screen_ratio and (flat_ratio > 0.35)

    return {
        "width": w,
        "height": h,
        "short_side": short_side,
        "megapixels": megapixels,
        "sharpness": round(sharpness, 1),
        "is_jpeg": is_jpeg,
        "jpeg_quality": jpeg_quality,
        "is_screenshot": is_screenshot,
    }


def compute_ela_map(img: Image.Image, quality: int = 90, scale: float = 15.0) -> Tuple[np.ndarray, float, Optional[BBox]]:
    """
    Computes Error Level Analysis:
    Recompresses image as JPEG at specified quality, computes difference.
    Returns (ela_grayscale_array, anomaly_score, largest_region_bbox).
    """
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf)

    diff = ImageChops.difference(img, recompressed)
    diff_arr = np.clip(np.asarray(diff).astype("float32") * scale, 0, 255).astype("uint8")

    # Grayscale difference
    gray_diff = cv2.cvtColor(diff_arr, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray_diff, (9, 9), 0)

    # Robust threshold using median + k * MAD
    median = np.median(blurred)
    mad = np.median(np.abs(blurred - median))
    threshold_val = median + 3.0 * (mad + 1e-4)

    mask = (blurred > threshold_val).astype("uint8") * 255
    anomaly_fraction = float(np.sum(mask > 0) / (mask.shape[0] * mask.shape[1]))

    # Locate largest anomalous connected component
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_bbox: Optional[BBox] = None
    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area > 400: # Ignore tiny specks
            x, y, bw, bh = cv2.boundingRect(c)
            img_w, img_h = img.size
            largest_bbox = BBox(
                page=0,
                x=round(x / img_w, 4),
                y=round(y / img_h, 4),
                w=round(bw / img_w, 4),
                h=round(bh / img_h, 4),
            )

    return gray_diff, min(1.0, anomaly_fraction * 8.0), largest_bbox


def compute_noise_residual(img: Image.Image, block_size: int = 64) -> Tuple[float, np.ndarray]:
    """
    Measures consistency of high-frequency noise variance across spatial blocks.
    Inconsistent variance indicates composited or spliced regions.
    """
    np_img = np.array(img)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    denoised = cv2.medianBlur(gray, 3)
    residual = cv2.absdiff(gray, denoised)

    h, w = residual.shape
    variances = []
    variance_map = np.zeros((h // block_size, w // block_size), dtype=np.float32)

    for i in range(0, h - block_size + 1, block_size):
        for j in range(0, w - block_size + 1, block_size):
            block = residual[i : i + block_size, j : j + block_size]
            var = float(np.var(block))
            variances.append(var)
            variance_map[i // block_size, j // block_size] = var

    if not variances:
        return 0.0, np.zeros((10, 10), dtype=np.uint8)

    med = np.median(variances)
    mad = np.median(np.abs(variances - med))
    dispersion = mad / (med + 1e-4)
    normalized_score = min(1.0, float(dispersion / 1.5))

    # Resize variance map to original image dimensions
    heatmap = cv2.resize(variance_map, (w, h), interpolation=cv2.INTER_CUBIC)
    heatmap_norm = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    return normalized_score, heatmap_norm


def save_forensic_heatmap(
    img: Image.Image,
    ela_map: np.ndarray,
    noise_map: np.ndarray,
    output_path: Path,
) -> Path:
    """
    Blends ELA and noise residuals into a heat map, color-mapped via JET,
    and blended with the original photo.
    """
    w, h = img.size
    ela_resized = cv2.resize(ela_map, (w, h), interpolation=cv2.INTER_LINEAR)
    noise_resized = cv2.resize(noise_map, (w, h), interpolation=cv2.INTER_LINEAR)

    combined = cv2.addWeighted(ela_resized, 0.65, noise_resized, 0.35, 0)
    colored_heatmap = cv2.applyColorMap(combined, cv2.COLORMAP_JET)

    np_img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    overlay = cv2.addWeighted(np_img_bgr, 0.60, colored_heatmap, 0.40, 0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), overlay)
    return output_path
