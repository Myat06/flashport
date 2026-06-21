import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.core.ceisa_gateway import simulate_submission
from app.database import get_db
from app.models.declaration import CeisaSubmission, Declaration, JalurType
from app.schemas.declaration import CeisaSubmitRequest, CeisaSubmitResponse, CeisaSubmissionOut
from app.services.fcm import send_ceisa_result

router = APIRouter(prefix="/ceisa", tags=["ceisa"])


@router.post("/submit", response_model=CeisaSubmitResponse)
async def submit_to_ceisa(body: CeisaSubmitRequest, db: Session = Depends(get_db)):
    declaration = db.query(Declaration).filter(Declaration.id == body.declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")

    fields = {f.field_name: f.field_value for f in declaration.fields}

    result = simulate_submission(
        declaration_id=str(declaration.id),
        risk_score=declaration.risk_score or 0,
        fields=fields,
    )

    submission = CeisaSubmission(
        declaration_id=declaration.id,
        submitted_by=body.submitted_by,
        jalur=JalurType(result["jalur"]),
        response_code=result["response_code"],
        response_message=result["response_message"],
        raw_response=result,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Fire push notification to operator (non-blocking)
    asyncio.create_task(send_ceisa_result(
        fcm_token=declaration.fcm_token or "",
        jalur=result["jalur"],
        ceisa_reference=result.get("ceisa_reference", submission.id.hex[:8].upper()),
        project_id=settings.fcm_project_id,
        service_account_json=settings.fcm_service_account_json,
    ))

    return CeisaSubmitResponse(
        submission_id=submission.id,
        declaration_id=declaration.id,
        jalur=JalurType(result["jalur"]),
        response_code=result["response_code"],
        response_message=result["response_message"],
    )


@router.get("/submissions", response_model=list[CeisaSubmissionOut])
def list_submissions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(CeisaSubmission)
        .order_by(CeisaSubmission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    results = []
    for row in rows:
        results.append(CeisaSubmissionOut(
            id=row.id,
            declaration_id=row.declaration_id,
            submitted_by=row.submitted_by,
            submitted_at=row.submitted_at,
            jalur=row.jalur,
            response_code=row.response_code,
            response_message=row.response_message,
            ceisa_reference=row.raw_response.get("ceisa_reference") if row.raw_response else None,
            document_type=row.declaration.document_type if row.declaration else None,
            risk_score=row.declaration.risk_score if row.declaration else None,
        ))
    return results
