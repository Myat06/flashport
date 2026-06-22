from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration, ReviewStatus

router = APIRouter(prefix="/sla", tags=["sla"])

SLA_HOURS = 24  # target review time


@router.get("")
def get_sla_metrics(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    declarations = db.query(Declaration).all()

    total = len(declarations)
    pending = [d for d in declarations if (d.review_status or ReviewStatus.pending) == ReviewStatus.pending]
    reviewed = [d for d in declarations if d.reviewed_at is not None]

    # Average review time (hours) for reviewed declarations
    review_times = []
    for d in reviewed:
        if d.synced_at and d.reviewed_at:
            delta = (d.reviewed_at.replace(tzinfo=None) - d.synced_at.replace(tzinfo=None)).total_seconds() / 3600
            review_times.append(delta)

    avg_review_hours = round(sum(review_times) / len(review_times), 1) if review_times else None

    # Overdue: pending declarations older than SLA_HOURS
    overdue = [
        {
            "id": str(d.id),
            "document_type": d.document_type.value if d.document_type else None,
            "operator_id": d.operator_id,
            "synced_at": d.synced_at.isoformat() if d.synced_at else None,
            "hours_pending": round(
                (now - d.synced_at.replace(tzinfo=None)).total_seconds() / 3600, 1
            ) if d.synced_at else None,
        }
        for d in pending
        if d.synced_at and (now - d.synced_at.replace(tzinfo=None)).total_seconds() / 3600 > SLA_HOURS
    ]

    # Throughput: declarations reviewed per day (last 7 days)
    daily = {}
    for d in reviewed:
        if d.reviewed_at:
            day = d.reviewed_at.date().isoformat()
            daily[day] = daily.get(day, 0) + 1

    return {
        "sla_target_hours": SLA_HOURS,
        "total_declarations": total,
        "pending_review": len(pending),
        "reviewed": len(reviewed),
        "overdue_count": len(overdue),
        "overdue": overdue,
        "avg_review_hours": avg_review_hours,
        "daily_throughput": daily,
    }
