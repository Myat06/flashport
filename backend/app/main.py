from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.api import auth, audit, ceisa, declarations, export, hs_codes, operators, risk_rules, sla, sync, watchlist, ws
from app.api.auth import hash_pin, verify_token

# Import all models so create_all picks up every table
from app.models import declaration  # noqa: F401
from app.models import operator as operator_model  # noqa: F401
from app.models import audit as audit_model  # noqa: F401
from app.models import watchlist as watchlist_model  # noqa: F401
from app.models import risk_rule as risk_rule_model  # noqa: F401
from app.models import hs_code as hs_code_model  # noqa: F401

Base.metadata.create_all(bind=engine)


def _seed_operators() -> None:
    from app.models.operator import Operator

    db = SessionLocal()
    try:
        if db.query(Operator).count() > 0:
            return
        seed = [
            ("CDP-001", "Ahmad Fauzi", "1234"),
            ("CDP-002", "Budi Santoso", "5678"),
            ("CDP-003", "Citra Dewi", "9012"),
        ]
        for emp_id, name, pin in seed:
            db.add(Operator(employee_id=emp_id, name=name, pin_hash=hash_pin(pin)))
        db.commit()
    finally:
        db.close()


_seed_operators()

app = FastAPI(
    title="FlashPort API",
    description="AI-powered customs declaration backend — Cikarang Dry Port",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PROTECTED = ("/sync", "/declarations", "/ceisa", "/audit", "/watchlist", "/risk-rules", "/hs-codes", "/operators", "/sla", "/export")


@app.middleware("http")
async def auth_check(request: Request, call_next):
    # Allow CORS preflight through — browser sends OPTIONS before every request
    if request.method == "OPTIONS":
        return await call_next(request)

    if not any(request.url.path.startswith(p) for p in _PROTECTED):
        return await call_next(request)

    # Accept X-API-Key (mobile) or Bearer JWT (web dashboard)
    if request.headers.get("X-API-Key", "") == settings.api_key:
        return await call_next(request)

    bearer = request.headers.get("Authorization", "")
    if bearer.startswith("Bearer ") and verify_token(bearer[7:]):
        return await call_next(request)

    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})


app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(declarations.router)
app.include_router(ceisa.router)
app.include_router(ws.router)
app.include_router(audit.router)
app.include_router(watchlist.router)
app.include_router(risk_rules.router)
app.include_router(hs_codes.router)
app.include_router(operators.router)
app.include_router(sla.router)
app.include_router(export.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "flashport-backend"}
