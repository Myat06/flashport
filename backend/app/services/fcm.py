"""FCM HTTP v1 push notification sender.

Requires FCM_SERVICE_ACCOUNT_JSON path in .env pointing to a Firebase
service account JSON file (Firebase console → Project Settings →
Service Accounts → Generate new private key).

Skips gracefully if not configured — no crash, just a log warning.
"""
import logging

import httpx

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

_JALUR_EMOJI = {"hijau": "✅", "kuning": "⚠️", "merah": "🔴"}
_JALUR_LABEL = {"hijau": "Jalur Hijau", "kuning": "Jalur Kuning", "merah": "Jalur Merah"}


def _get_access_token(service_account_json: str) -> str:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        service_account_json, scopes=_SCOPES
    )
    creds.refresh(GoogleRequest())
    return creds.token


async def send_ceisa_result(
    fcm_token: str,
    jalur: str,
    ceisa_reference: str,
    project_id: str,
    service_account_json: str,
) -> None:
    if not service_account_json or not fcm_token:
        logger.warning("FCM skipped — FCM_SERVICE_ACCOUNT_JSON or fcm_token not set.")
        return

    try:
        access_token = _get_access_token(service_account_json)
        emoji = _JALUR_EMOJI.get(jalur, "")
        label = _JALUR_LABEL.get(jalur, jalur.title())

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "message": {
                        "token": fcm_token,
                        "notification": {
                            "title": f"CEISA: {emoji} {label}",
                            "body": f"Ref {ceisa_reference} telah diproses oleh Bea Cukai.",
                        },
                        "android": {"priority": "high"},
                        "apns": {"headers": {"apns-priority": "10"}},
                    }
                },
            )
            resp.raise_for_status()
            logger.info("FCM sent to %s — jalur %s", fcm_token[:20], jalur)
    except Exception as exc:
        logger.warning("FCM send failed (non-fatal): %s", exc)
