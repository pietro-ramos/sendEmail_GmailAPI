import base64
import re
from datetime import datetime
from typing import Any

from config import (
    ASSUNTO,
    BOUNCE_AFTER_DATE_GMAIL,
    BOUNCE_MAX_MESSAGES,
    GMAIL_BOUNCE_CREDENTIALS_FILE,
    GMAIL_BOUNCE_TOKEN_FILE,
)
from services.auth import Auth


GMAIL_READONLY_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
)
UNKNOWN_RECIPIENT = "Destinatário desconhecido"


def _normalize_text(body: str) -> tuple[str, str]:
    raw_text = (body or "").replace("=\r\n", "").replace("=\n", "")
    plain_text = re.sub(r"<[^>]+>", " ", raw_text)
    return raw_text, plain_text


def _build_bounce_query() -> str:
    after_date = datetime.fromisoformat(
        BOUNCE_AFTER_DATE_GMAIL
    ).strftime("%Y/%m/%d")
    subjects = (
        "Delivery Status Notification",
        "Delivery Status Notification (Failure)",
        "Problema ao entregar o e-mail - retorno ao remetente",
        f"Undeliverable: {ASSUNTO}",
    )
    subject_query = " OR ".join(
        f'subject:"{subject}"' for subject in dict.fromkeys(subjects)
    )
    return f"({subject_query}) after:{after_date}"


def get_gmail_service_readonly():
    return Auth(
        token_path=GMAIL_BOUNCE_TOKEN_FILE,
        credentials_path=GMAIL_BOUNCE_CREDENTIALS_FILE,
        scopes=GMAIL_READONLY_SCOPES,
    ).get_service()


def _extract_recipient_from_body(body: str) -> str:
    raw_body, plain_body = _normalize_text(body)
    patterns = (
        r"Final-Recipient:\s*rfc822;\s*([^\s<>]+)",
        r"X-Failed-Recipients:\s*([^\s<>]+)",
        r"Endereço de e-mail\s+([^\s<>]+)\s+não pôde ser encontrado",
        r"Usuário desconhecido:\s*([^\n]+)",
        r"Não foi possível entregar a sua mensagem para\s+([^\s<>\n]+)",
        r"([\w.%+\-]+@[\w.\-]+\.[A-Za-z]{2,})",
    )
    for pattern in patterns:
        for source in (raw_body, plain_body):
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip(".,;")
    return UNKNOWN_RECIPIENT


def _extract_bounce_reason(body: str) -> str:
    raw_body, plain_body = _normalize_text(body)
    patterns = (
        (
            r"Caixa de entrada do destinatário está cheia",
            "Caixa de entrada do destinatário está cheia",
        ),
        (
            r"The recipient's inbox is out of storage space",
            "Caixa de entrada do destinatário está cheia",
        ),
        (r"User unknown", "Usuário desconhecido"),
        (r"Endereço não encontrado", "Endereço não encontrado"),
        (r"relay access denied", "Relay access denied"),
        (
            r"Action:\s*failed[\s\S]*?Diagnostic-Code:\s*smtp;\s*([^\n]+)",
            None,
        ),
    )
    for pattern, fixed_reason in patterns:
        for source in (raw_body, plain_body):
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                return fixed_reason or match.group(1).strip()
    return "Motivo não identificado"


def _decode_body(data: str) -> str:
    if not data:
        return ""
    padded = data + ("=" * (-len(data) % 4))
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")


def _get_body_from_payload(payload: dict[str, Any]) -> str:
    body = _decode_body(payload.get("body", {}).get("data", ""))
    for part in payload.get("parts", []):
        body += _get_body_from_payload(part)
    return body


def buscar_bounces_gmail(service=None) -> list[dict[str, str]]:
    service = service or get_gmail_service_readonly()
    query = _build_bounce_query()
    page_token = None
    records = []

    while len(records) < BOUNCE_MAX_MESSAGES:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                pageToken=page_token,
                maxResults=min(500, BOUNCE_MAX_MESSAGES),
            )
            .execute()
        )
        messages = response.get("messages", [])
        if not messages:
            break

        for message in messages:
            if len(records) >= BOUNCE_MAX_MESSAGES:
                break
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=message["id"], format="full")
                .execute()
            )
            payload = detail.get("payload", {})
            headers = {
                header.get("name", "").lower(): header.get("value", "")
                for header in payload.get("headers", [])
            }
            body = _get_body_from_payload(payload)
            recipient = (
                headers.get("x-failed-recipients")
                or _extract_recipient_from_body(body)
            )
            if recipient == UNKNOWN_RECIPIENT:
                continue
            records.append(
                {
                    "Destinatario": recipient,
                    "Motivo do bounce": _extract_bounce_reason(body),
                }
            )

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"Bounces Gmail encontrados: {len(records)}.")
    return records
