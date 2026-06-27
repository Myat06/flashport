from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.declaration import ConfidenceLevel, DocType, JalurType, ReviewStatus, RiskLevel


class FieldBbox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class FieldValidationResult(BaseModel):
    field_name: str
    value: Optional[str] = None
    is_valid: bool
    priority: str           # critical | important | optional
    message: Optional[str] = None
    bbox: Optional[FieldBbox] = None


class SyncPayload(BaseModel):
    scan_id: UUID
    scanned_at: datetime
    document_type: DocType
    operator_id: Optional[str] = None
    device_id: Optional[str] = None
    fcm_token: Optional[str] = None
    ml_kit_text: str
    image_b64: str


class ExtractedFields(BaseModel):
    """Fully dynamic: any field_key/value pairs from field_definitions are allowed."""
    model_config = ConfigDict(extra="allow")


class ShapEntry(BaseModel):
    feature: str
    label: str
    value: float
    shap_value: float
    direction: str   # "increase" | "decrease"


class SyncResponse(BaseModel):
    declaration_id: UUID
    confidence_badge: ConfidenceLevel
    risk_score: int
    risk_badge: RiskLevel
    extracted_fields: ExtractedFields
    flagged_fields: list[str]
    ceisa_ready: bool
    shap_values: list[ShapEntry] = []
    extraction_method: str = "regex"
    validation_results: list[FieldValidationResult] = []
    image_width: Optional[int] = None
    image_height: Optional[int] = None


class OcrPreviewResponse(BaseModel):
    confidence_badge: ConfidenceLevel
    risk_score: int
    risk_badge: RiskLevel
    extracted_fields: ExtractedFields
    flagged_fields: list[str]


class DeclarationUpdate(BaseModel):
    field_name: str
    field_value: str
    reviewed_by: Optional[str] = None


class ReviewRequest(BaseModel):
    status: ReviewStatus
    note: Optional[str] = None
    reviewed_by: Optional[str] = "manager"


class CeisaSubmitRequest(BaseModel):
    declaration_id: UUID
    submitted_by: Optional[str] = None


class CeisaSubmitResponse(BaseModel):
    submission_id: UUID
    declaration_id: UUID
    jalur: JalurType
    response_code: str
    response_message: str


class CeisaSubmissionOut(BaseModel):
    id: UUID
    declaration_id: UUID
    submitted_by: Optional[str]
    submitted_at: datetime
    jalur: JalurType
    response_code: str
    response_message: str
    ceisa_reference: Optional[str]
    document_type: Optional[DocType]
    risk_score: Optional[int]

    class Config:
        from_attributes = True


class DeclarationOut(BaseModel):
    id: UUID
    scan_id: UUID
    document_type: DocType
    operator_id: Optional[str]
    scanned_at: datetime
    synced_at: Optional[datetime]
    confidence_badge: Optional[ConfidenceLevel]
    risk_score: Optional[int]
    risk_badge: Optional[RiskLevel]
    extracted_fields: Optional[ExtractedFields]
    flagged_fields: list[str]
    ceisa_ready: bool
    review_status: Optional[ReviewStatus] = ReviewStatus.pending
    review_note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
