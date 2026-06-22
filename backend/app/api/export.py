import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/declarations.csv")
def export_declarations_csv(
    status: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Declaration).order_by(Declaration.created_at.desc())

    if status:
        q = q.filter(Declaration.review_status == status)
    if from_date:
        q = q.filter(Declaration.scanned_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(Declaration.scanned_at <= datetime.fromisoformat(to_date))

    rows = q.limit(5000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Declaration ID", "Scan ID", "Document Type", "Operator",
        "Scanned At", "Confidence", "Risk Score", "Risk Badge",
        "Review Status", "Reviewed By", "Reviewed At",
        "CEISA Ready", "Created At",
        "HS Code", "Invoice Value", "Container ID", "Importer", "Exporter",
        "Net Weight", "Gross Weight", "Vessel", "Port of Origin",
    ])

    for d in rows:
        fields = {f.field_name: f.field_value for f in d.fields}
        writer.writerow([
            str(d.id), str(d.scan_id),
            d.document_type.value if d.document_type else "",
            d.operator_id or "",
            d.scanned_at.isoformat() if d.scanned_at else "",
            d.confidence_badge.value if d.confidence_badge else "",
            d.risk_score or 0,
            d.risk_badge.value if d.risk_badge else "",
            d.review_status.value if d.review_status else "pending",
            d.reviewed_by or "",
            d.reviewed_at.isoformat() if d.reviewed_at else "",
            d.ceisa_ready,
            d.created_at.isoformat() if d.created_at else "",
            fields.get("hs_code", ""),
            fields.get("invoice_value", ""),
            fields.get("container_id", ""),
            fields.get("importer", ""),
            fields.get("exporter", ""),
            fields.get("net_weight", ""),
            fields.get("gross_weight", ""),
            fields.get("vessel_name", ""),
            fields.get("port_of_origin", ""),
        ])

    output.seek(0)
    filename = f"flashport_declarations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
