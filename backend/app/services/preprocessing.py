import base64

import cv2
import numpy as np

_PDF_MAGIC = b'%PDF'


def is_pdf(image_b64: str) -> bool:
    data = base64.b64decode(image_b64[:16])
    return data[:4] == _PDF_MAGIC


def decode_image(image_b64: str) -> np.ndarray:
    """Decode a single image or the first page of a PDF."""
    data = base64.b64decode(image_b64)
    if data[:4] == _PDF_MAGIC:
        return _pdf_to_ndarray(data, first_page=1, last_page=1)[0]
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def decode_pdf_pages(image_b64: str) -> list[np.ndarray]:
    """Decode all pages of a PDF as BGR images."""
    data = base64.b64decode(image_b64)
    return _pdf_to_ndarray(data)


def extract_pdf_text_direct(image_b64: str) -> str | None:
    """
    Extract text directly from a digital PDF without OCR.

    Uses pypdf to read the PDF text layer directly — much more accurate than
    running Tesseract on a table-heavy digital PDF.
    Returns None if the PDF has no text layer (scanned image PDF) so the
    caller can fall back to Tesseract OCR.
    """
    try:
        import io
        from pypdf import PdfReader
        pdf_bytes = base64.b64decode(image_b64)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
        combined = "\n".join(pages_text).strip()
        if len(combined) > 50:
            return combined
        return None
    except Exception:
        return None


def _pdf_to_ndarray(pdf_bytes: bytes, first_page: int = 1, last_page: int | None = None) -> list[np.ndarray]:
    from pdf2image import convert_from_bytes  # noqa: PLC0415
    kwargs = {"dpi": 200, "first_page": first_page}
    if last_page is not None:
        kwargs["last_page"] = last_page
    pages = convert_from_bytes(pdf_bytes, **kwargs)
    return [np.array(p.convert('RGB'))[:, :, ::-1] for p in pages]  # RGB → BGR


def preprocess(image: np.ndarray) -> np.ndarray:
    """
    Adaptive preprocessing pipeline:
    - Clean / high-contrast images (digital scans, good phone photos):
        grayscale only — thresholding would destroy them
    - Noisy / low-contrast images (bad photos, dark shadows):
        full pipeline: grayscale → denoise → threshold → deskew
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect image quality:
    # Clean document (digital render or good photo): most pixels are very white (>200)
    # Noisy/dark photo: fewer white pixels, more mid-gray values
    white_ratio = float((gray > 200).mean())
    if white_ratio > 0.55:
        # Already clean — white background, dark text — skip aggressive preprocessing
        return gray

    # Low contrast image — apply full preprocessing for phone photos
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    deskewed = _deskew(thresh)
    return deskewed


def _deskew(image: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:
        return image
    h, w = image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
