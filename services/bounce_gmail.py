import base64
import os
import re
from datetime import datetime
from typing import Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import ASSUNTO_GMAIL, BOUNCE_AFTER_DATE_GMAIL


def _normalize_text(body: str) -> tuple[str, str]:
    raw_text = (body or "").replace("=\n", "\n")
    plain_text = re.sub(r"<[^>]+>", " ", raw_text)
    return raw_text, plain_text


def _build_bounce_query() -> str:
    after_date = datetime.fromisoformat(BOUNCE_AFTER_DATE_GMAIL).strftime("%Y/%m/%d")
    subjects = [
        "Delivery Status Notification",
        "Delivery Status Notification (Failure)",
        "Problema ao entregar o e-mail - retorno ao remetente",
        f"Undeliverable: {ASSUNTO_GMAIL}",
        ASSUNTO_GMAIL,
    ]
    unique_subjects = []
    for subject in subjects:
        subject = (subject or "").strip()
        if subject and subject not in unique_subjects:
            unique_subjects.append(subject)
    subject_query = " OR ".join(f'subject:"{subject}"' for subject in unique_subjects)
    return f"{subject_query} after:{after_date}"


def get_gmail_service_readonly():
    creds = None
    token_file = "token.json"
    credentials_file = "credentials.json"

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, ["https://www.googleapis.com/auth/gmail.readonly"]
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _extract_recipient_from_body(body: str) -> str:
    raw_body, plain_body = _normalize_text(body)
    patterns = [
        r"Endereço de e-mail ([^ ]+) não pôde ser encontrado",
        r"Usuário desconhecido: ([^\n]+)",
        r"mensagem para <a.*?><b>([^<]+)</b></a>",
        r"Final-Recipient: rfc822; ([^\n]+)",
        r"Não foi possível entregar a sua mensagem para\s+([^\s<>\n]+)",
        r"(\S+@\S+\.\S+)",
    ]
    for pattern in patterns:
        for source in (raw_body, plain_body):
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip(".")
    return "Destinatário desconhecido"


def _extract_bounce_reason(body: str) -> str:
    raw_body, plain_body = _normalize_text(body)
    patterns = [
        r"Caixa de entrada do destinatário está cheia",
        r"Caixa de entrada do destinatário está cheia ou está recebendo muitos e-mails",
        r"The recipient's inbox is out of storage space",
        r"O Gmail tentará novamente por mais \d+ horas",
        r"452 4.2.2.*The recipient's inbox is out of storage space",
        r"Ocorreu um problema temporário na entrega da mensagem para [^\n]+",
        r"Sua mensagem não foi entregue a [^ ]+ porque ([^\n]+)",
        r"Action: failed\nDiagnostic-Code: smtp; ([^\n]+)",
        r"Endereço não encontrado",
        r"The recipient server did not accept our requests to connect. ([^\n]+)",
        r"The recipient's mailbox is full",
        r"User unknown",
        r"Não foi possível entregar a sua mensagem para\s+([^\s<>\n]+)",
        r"n[ãa]o\s+tem\s+autoriz",
        r"remetente\s+n[ãa]o\s+autorizado",
        r"not permitted to relay",
        r"relay access denied",
        r"550\s+5\.7\.367[\s\S]*?relay",
    ]
    for pattern in patterns:
        for source in (raw_body, plain_body):
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                if pattern == r"Não foi possível entregar a sua mensagem para\s+([^\s<>\n]+)":
                    return f"Não foi possível entregar a sua mensagem para {match.group(1).strip().strip('.')}"
                if pattern in {r"n[ãa]o\s+tem\s+autoriz", r"remetente\s+n[ãa]o\s+autorizado"}:
                    return "Remetente não autorizado para retransmissão"
                if pattern in {r"not permitted to relay", r"relay access denied"}:
                    return "Relay access denied"
                if pattern == r"550\s+5\.7\.367[\s\S]*?relay":
                    return "550 5.7.367 not permitted to relay"
                return match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
    return "Motivo desconhecido"


def _extract_body_from_parts(parts) -> str:
    body = ""
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type in ["text/plain", "text/html"]:
            body_data = part.get("body", {}).get("data", "")
            if body_data:
                body += base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
        elif "parts" in part:
            body += _extract_body_from_parts(part.get("parts", []))
    return body


def _get_body_from_payload(payload) -> str:
    if "parts" in payload:
        return _extract_body_from_parts(payload["parts"])
    return _extract_body_from_parts([payload])


def buscar_bounces_gmail() -> List[Dict[str, str]]:
    service = get_gmail_service_readonly()
    query = _build_bounce_query()
    response = service.users().messages().list(userId="me", q=query).execute()
    messages = response.get("messages", [])
    next_page_token = response.get("nextPageToken", None)

    bounce_records = []
    emails_without_recipient = []

    while messages:
        for message in messages:
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            failed_recipient = None
            for header in headers:
                if header["name"] == "X-Failed-Recipients":
                    failed_recipient = header["value"]
                    break

            body = _get_body_from_payload(payload)
            if not failed_recipient:
                failed_recipient = _extract_recipient_from_body(body)
            bounce_reason = _extract_bounce_reason(body)

            if failed_recipient == "Destinatário desconhecido":
                emails_without_recipient.append(message["id"])

            if failed_recipient:
                bounce_records.append(
                    {
                        "Destinatario": failed_recipient,
                        "Motivo do bounce": bounce_reason,
                    }
                )

        if next_page_token:
            response = service.users().messages().list(
                userId="me", q=query, pageToken=next_page_token
            ).execute()
            messages = response.get("messages", [])
            next_page_token = response.get("nextPageToken", None)
        else:
            break

    if emails_without_recipient:
        with open("emails_sem_destinatario.txt", "w", encoding="utf-8") as file:
            for email_id in emails_without_recipient:
                file.write(f"E-mail ID: {email_id}\n")
        print("Relatório de e-mails sem destinatário salvo em 'emails_sem_destinatario.txt'.")

    return bounce_records
