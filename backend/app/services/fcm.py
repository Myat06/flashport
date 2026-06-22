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

_LANE_EMOJI = {"hijau": "✅", "kuning": "⚠️", "merah": "🔴"}
_LANE_LABEL = {"hijau": "Green Lane", "kuning": "Yellow Lane", "merah": "Red Lane"}


def _get_access_token(service_account_json: str) -> str:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        service_account_json, scopes=_SCOPES
    )
    creds.refresh(GoogleRequest())
    return creds.token


async def _send(fcm_token: str, title: str, body: str, project_id: str, service_account_json: str) -> None:
    if not service_account_json or not fcm_token:
        logger.warning("FCM skipped — FCM_SERVICE_ACCOUNT_JSON or fcm_token not set.")
        return
    try:
        access_token = _get_access_token(service_account_json)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "message": {
                        "token": fcm_token,
                        "notification": {"title": title, "body": body},
                        "android": {"priority": "high"},
                        "apns": {"headers": {"apns-priority": "10"}},
                    }
                },
            )
            resp.raise_for_status()
            logger.info("FCM sent to %s — %s", fcm_token[:20], title)
    except Exception as exc:
        logger.warning("FCM send failed (non-fatal): %s", exc)


async def send_ceisa_result(
    fcm_token: str, jalur: str, ceisa_reference: str, project_id: str, service_account_json: str,
) -> None:
    emoji = _LANE_EMOJI.get(jalur, "")
    label = _LANE_LABEL.get(jalur, jalur.title())
    await _send(
        fcm_token,
        title=f"CEISA: {emoji} {label}",
        body=f"Reference {ceisa_reference} has been processed by Customs.",
        project_id=project_id,
        service_account_json=service_account_json,
    )


async def send_review_result(
    fcm_token: str, status: str, note: str, project_id: str, service_account_json: str,
) -> None:
    icons = {"approved": "✅", "rejected": "❌"}
    titles = {"approved": "Declaration Approved", "rejected": "Declaration Rejected"}
    icon = icons.get(status, "📄")
    title = titles.get(status, f"Declaration {status.title()}")
    body = f'Manager note: "{note}"' if note else "Review completed by manager."
    await _send(fcm_token, title=f"{icon} {title}", body=body,
                project_id=project_id, service_account_json=service_account_json)
