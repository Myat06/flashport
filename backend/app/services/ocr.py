import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

_TESS_CONFIG = "--oem 3 --psm 6 -l eng+ind"


def run_tesseract(image: np.ndarray) -> str:
    pil_image = Image.fromarray(image)
    return pytesseract.image_to_string(pil_image, config=_TESS_CONFIG).strip()


def run_tesseract_with_boxes(
    raw_image: np.ndarray,
) -> tuple[str, list[dict], int, int]:
    """OCR an image and return text, word-level bounding boxes, and image dimensions.

    Bounding boxes are in the coordinate space of raw_image (original, pre-preprocessing).
    Text is extracted from the fully-preprocessed image for best quality.

    Returns: (text, word_data, image_width, image_height)
    word_data items: {text, x, y, w, h, conf}
    """
    from app.services.preprocessing import preprocess

    # Dimensions from the raw image — bbox coordinates will match these
    if raw_image.ndim == 3:
        img_h, img_w = raw_image.shape[:2]
        gray = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY)
    else:
        img_h, img_w = raw_image.shape
        gray = raw_image

    # Bounding boxes from grayscale (same pixel grid as original, no deskew)
    data = pytesseract.image_to_data(
        Image.fromarray(gray),
        config=_TESS_CONFIG,
        output_type=pytesseract.Output.DICT,
    )
    word_data: list[dict] = []
    for i in range(len(data["text"])):
        text = str(data["text"][i]).strip()
        conf = int(data["conf"][i])
        if text and conf > 0:
            word_data.append({
                "text": text,
                "x": int(data["left"][i]),
                "y": int(data["top"][i]),
                "w": int(data["width"][i]),
                "h": int(data["height"][i]),
                "conf": conf,
            })

    # Full-pipeline text for maximum extraction quality
    if raw_image.ndim == 2:
        raw_bgr = cv2.cvtColor(raw_image, cv2.COLOR_GRAY2BGR)
    else:
        raw_bgr = raw_image
    preprocessed = preprocess(raw_bgr)
    text = pytesseract.image_to_string(
        Image.fromarray(preprocessed), config=_TESS_CONFIG
    ).strip()

    return text, word_data, img_w, img_h


def compute_confidence(ml_kit_text: str, tesseract_text: str) -> tuple[float, str]:
    """Compute OCR confidence.

    With ML Kit text: Jaccard similarity between both engines.
    Without ML Kit (stubbed): text-quality heuristic on the Tesseract output —
    word count and alphabetic-character ratio reflect how clean the scanned image is.
    Returns (score 0.0-1.0, badge 'high'|'medium'|'low').
    """
    if not ml_kit_text:
        if not tesseract_text:
            return (0.0, "low")
        words       = tesseract_text.split()
        word_count  = len(words)
        alpha_ratio = sum(1 for c in tesseract_text if c.isalpha()) / max(len(tesseract_text), 1)
        if word_count >= 20 and alpha_ratio >= 0.50:
            return (0.88, "high")
        elif word_count >= 8 and alpha_ratio >= 0.35:
            return (0.65, "medium")
        return (0.30, "low")

    if not tesseract_text:
        return 0.0, "low"

    ml_words   = set(ml_kit_text.lower().split())
    tess_words = set(tesseract_text.lower().split())

    if not ml_words or not tess_words:
        return 0.0, "low"

    intersection = ml_words & tess_words
    union        = ml_words | tess_words
    jaccard      = len(intersection) / len(union)

    if jaccard >= 0.75:
        return jaccard, "high"
    elif jaccard >= 0.45:
        return jaccard, "medium"
    return jaccard, "low"
