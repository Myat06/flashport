import pytesseract
from PIL import Image
import numpy as np

from app.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def run_tesseract(image: np.ndarray) -> str:
    pil_image = Image.fromarray(image)
    config = "--oem 3 --psm 6 -l eng+ind"
    return pytesseract.image_to_string(pil_image, config=config).strip()


def compute_confidence(ml_kit_text: str, tesseract_text: str) -> tuple[float, str]:
    """Compare ML Kit and Tesseract outputs via Jaccard similarity.

    When ml_kit_text is empty (ML Kit stubbed), trust Tesseract alone at 0.85.
    Returns (score 0.0-1.0, badge 'high'|'medium'|'low').
    """
    if not ml_kit_text:
        return (0.85, "high") if tesseract_text else (0.0, "low")
    if not tesseract_text:
        return 0.0, "low"

    ml_words = set(ml_kit_text.lower().split())
    tess_words = set(tesseract_text.lower().split())

    if not ml_words or not tess_words:
        return 0.0, "low"

    intersection = ml_words & tess_words
    union = ml_words | tess_words
    jaccard = len(intersection) / len(union)

    if jaccard >= 0.75:
        return jaccard, "high"
    elif jaccard >= 0.45:
        return jaccard, "medium"
    return jaccard, "low"
