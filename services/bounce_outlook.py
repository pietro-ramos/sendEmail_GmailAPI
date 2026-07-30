import datetime
import html
import re
from collections.abc import Iterable
from typing import Any

import requests

from config import (
    BOUNCE_AFTER_DATE_OUTLOOK,
    BOUNCE_MAX_MESSAGES,
    BOUNCE_PAGE_SIZE,
    BOUNCE_REQUEST_TIMEOUT_SECONDS,
    CLIENT_ID,
    CLIENT_SECRET,
    REMETENTE,
    TENANT_ID,
)
from services.graph_auth import GraphAuth


UNKNOWN_RECIPIENT = "Destinatario desconhecido"
EMAIL_PATTERN = re.compile(
    r"[\w.%+\-]+@[\w.\-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)
NON_DELIVERY_SUBJECTS = (
    "Não é possível entregar:",
    "Nao e possivel entregar:",
    "Undeliverable:",
)


def _build_client() -> GraphAuth:
    missing = [
        name
        for name, value in {
            "GRAPH_TENANT_ID": TENANT_ID,
            "GRAPH_CLIENT_ID": CLIENT_ID,
            "GRAPH_CLIENT_SECRET": CLIENT_SECRET,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(
            f"Configuração Outlook incompleta: {', '.join(missing)}."
        )
    return GraphAuth(TENANT_ID, CLIENT_ID, CLIENT_SECRET)


def _normalize_email(value: str) -> str:
    return re.sub(
        r"\s+",
        "",
        str(value or "").replace("\u00a0", ""),
    ).strip().lower()


def _cutoff_odata() -> str:
    cutoff = datetime.datetime.fromisoformat(BOUNCE_AFTER_DATE_OUTLOOK)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=datetime.timezone.utc)
    return (
        cutoff.astimezone(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _odata_string(value: str) -> str:
    return value.replace("'", "''")


def _paged_request(
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    collected = []
    next_url = url
    next_params = params

    while next_url and len(collected) < BOUNCE_MAX_MESSAGES:
        response = requests.get(
            next_url,
            headers=headers,
            params=next_params,
            timeout=BOUNCE_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        collected.extend(data.get("value", []))
        next_url = data.get("@odata.nextLink")
        next_params = None

    return collected[:BOUNCE_MAX_MESSAGES]


def _list_messages(token: str) -> list[dict[str, Any]]:
    base_url = f"https://graph.microsoft.com/v1.0/users/{REMETENTE}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    messages = []
    seen = set()

    for subject in NON_DELIVERY_SUBJECTS:
        params = {
            "$top": BOUNCE_PAGE_SIZE,
            "$filter": (
                f"receivedDateTime ge {_cutoff_odata()} "
                f"and contains(subject,'{_odata_string(subject)}')"
            ),
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,receivedDateTime,bodyPreview,body",
        }
        try:
            results = _paged_request(base_url, headers, params)
        except requests.RequestException as exc:
            print(f"Consulta Outlook por assunto '{subject}' falhou: {exc}")
            continue

        for message in results:
            key = message.get("id")
            if not key or key in seen:
                continue
            seen.add(key)
            messages.append(message)
            if len(messages) >= BOUNCE_MAX_MESSAGES:
                return messages

    return messages


def _clean_message_text(text: str) -> str:
    clean = str(text or "").replace("=\r\n", "").replace("=\n", "")
    clean = re.sub(r"<br\s*/?>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(
        r"</(p|div|li|tr|td|h[1-6])>",
        "\n",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = html.unescape(clean).replace("\u00a0", " ")
    clean = re.sub(r"[ \t]+", " ", clean)
    return re.sub(r"\n\s+", "\n", clean).strip()


def _extract_recipient(
    text: str,
    destinatarios_alvo: Iterable[str] | None = None,
) -> str:
    emails_in_body = {
        _normalize_email(match.group(0).strip(".,;:<>[]()"))
        for match in EMAIL_PATTERN.finditer(_clean_message_text(text))
    }
    for target in destinatarios_alvo or []:
        normalized = _normalize_email(target)
        if normalized in emails_in_body:
            return normalized
    return UNKNOWN_RECIPIENT


def buscar_bounces_outlook(
    destinatarios_alvo: Iterable[str] | None = None,
) -> list[dict[str, str]]:
    messages = _list_messages(_build_client().get_token())
    bounces = []

    for message in messages:
        body = message.get("body", {}).get("content", "")
        text = body or message.get("bodyPreview", "")
        recipient = _extract_recipient(text, destinatarios_alvo)
        if recipient == UNKNOWN_RECIPIENT:
            continue
        bounces.append(
            {
                "Destinatario": recipient,
                "Motivo do bounce": (
                    "Retorno de não entrega encontrado no Outlook"
                ),
                "Recebido em": message.get("receivedDateTime", ""),
            }
        )

    print(
        f"Mensagens de não entrega analisadas: {len(messages)} | "
        f"bounces relacionados ao relatório: {len(bounces)}."
    )
    return bounces
