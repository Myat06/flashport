from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.declaration import ConfidenceLevel, DocType, JalurType, RiskLevel


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
    hs_code: Optional[str] = None
    invoice_value: Optional[str] = None
    container_id: Optional[str] = None
    importer: Optional[str] = None
    exporter: Optional[str] = None
    net_weight: Optional[str] = None
    gross_weight: Optional[str] = None
    vessel_name: Optional[str] = None
    port_of_origin: Optional[str] = None
    invoice_number: Optional[str] = None
    carton_count: Optional[str] = None


class SyncResponse(BaseModel):
    declaration_id: UUID
    confidence_badge: ConfidenceLevel
    risk_score: int
    risk_badge: RiskLevel
    extracted_fields: ExtractedFields
    flagged_fields: list[str]
    ceisa_ready: bool


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
    created_at: datetime

    class Config:
        from_attributes = True
