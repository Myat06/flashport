"""Mock CEISA Host-to-Host gateway for Phase 1 demo.

Returns realistic Jalur responses based on risk score.
Real CEISA credentials and live integration happen in Phase 2 (August).
"""
import uuid
from datetime import datetime

from app.models.declaration import JalurType


def simulate_submission(declaration_id: str, risk_score: int, fields: dict) -> dict:
    """Simulate CEISA response for a given risk score."""
    jalur, code, message = _determine_jalur(risk_score, fields)

    return {
        "submission_id": str(uuid.uuid4()),
        "declaration_id": declaration_id,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "jalur": jalur.value,
        "response_code": code,
        "response_message": message,
        "ceisa_reference": f"PIB-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
    }


def _determine_jalur(risk_score: int, fields: dict) -> tuple[JalurType, str, str]:
    if risk_score < 30:
        return (
            JalurType.hijau,
            "SP2-200",
            "Dokumen diterima. Peti kemas disetujui untuk pengeluaran segera (Jalur Hijau).",
        )
    elif risk_score < 70:
        missing = [k for k, v in fields.items() if not v]
        detail = f"Field tidak lengkap: {', '.join(missing[:3])}" if missing else "Data memerlukan verifikasi dokumen"
        return (
            JalurType.kuning,
            "SP2-412",
            f"Dokumen ditahan untuk verifikasi manual (Jalur Kuning). {detail}.",
        )
    else:
        return (
            JalurType.merah,
            "SP2-500",
            "Peti kemas ditahan untuk pemeriksaan fisik (Jalur Merah). Risiko anomali terdeteksi. Harap hubungi petugas Bea Cukai.",
        )
