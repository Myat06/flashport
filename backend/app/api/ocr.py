from fastapi import APIRouter
from pydantic import BaseModel

from app.models.declaration import ConfidenceLevel, RiskLevel
from app.schemas.declaration import ExtractedFields, OcrPreviewResponse
from app.services.extractor import extract_fields
from app.services.ocr import compute_confidence, run_tesseract
from app.services.preprocessing import decode_image, decode_pdf_pages, is_pdf, preprocess
from app.services.risk_scorer import score as compute_risk

router = APIRouter(prefix="/ocr", tags=["ocr"])


class OcrPreviewRequest(BaseModel):
    document_type: str
    ml_kit_text: str = ""
    image_b64: str


@router.post("/preview", response_model=OcrPreviewResponse)
def preview_ocr(body: OcrPreviewRequest):
    if is_pdf(body.image_b64):
        images = decode_pdf_pages(body.image_b64)
        text = "\n".join(run_tesseract(preprocess(img)) for img in images)
    else:
        text = run_tesseract(preprocess(decode_image(body.image_b64)))

    _, confidence_badge = compute_confidence(body.ml_kit_text, text)
    extraction = extract_fields(text)
    risk_score, risk_badge, flagged = compute_risk(extraction, confidence_badge)

    return OcrPreviewResponse(
        confidence_badge=ConfidenceLevel(confidence_badge),
        risk_score=risk_score,
        risk_badge=RiskLevel(risk_badge),
        extracted_fields=ExtractedFields(**extraction.to_dict()),
        flagged_fields=flagged,
    )
