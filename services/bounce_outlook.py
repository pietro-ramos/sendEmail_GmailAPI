import datetime
import html
import re
from typing import Any, Dict, Iterable, List, Optional, Set

import requests

from config import (
    BOUNCE_AFTER_DATE_OUTLOOK,
    BOUNCE_MAX_MESSAGES,
    BOUNCE_PAGE_SIZE,
    CLIENT_ID,
    CLIENT_SECRET,
    REMETENTE,
    TENANT_ID,
)
from services.graph_auth import GraphAuth

DESTINATARIO_DESCONHECIDO = "Destinatario desconhecido"
EMAIL_PATTERN = re.compile(r"[\w.%+\-]+@[\w.\-]+\.[A-Za-z]{2,}", re.IGNORECASE)
ASSUNTOS_NAO_ENTREGA = (
    "Não é possível entregar:",
    "Nao e possivel entregar:",
)


def _build_client() -> GraphAuth:
    return GraphAuth(TENANT_ID, CLIENT_ID, CLIENT_SECRET)


def _normalize_email(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").replace("\u00a0", "")).strip().lower()


def _data_corte() -> datetime.datetime:
    data_corte = datetime.datetime.fromisoformat(BOUNCE_AFTER_DATE_OUTLOOK)
    if data_corte.tzinfo is None:
        data_corte = data_corte.replace(tzinfo=datetime.timezone.utc)
    return data_corte


def _data_corte_odata() -> str:
    return (
        _data_corte()
        .astimezone(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _odata_string(value: str) -> str:
    return value.replace("'", "''")


def _paged_request(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    next_url = url
    next_params = params

    while True:
        resp = requests.get(next_url, headers=headers, params=next_params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        collected.extend(data.get("value", []))
        if len(collected) >= BOUNCE_MAX_MESSAGES:
            break
        next_link = data.get("@odata.nextLink")
        if not next_link:
            break
        next_url = next_link
        next_params = None

    return collected[:BOUNCE_MAX_MESSAGES]


def _list_messages(token: str) -> List[Dict[str, Any]]:
    base_url = f"https://graph.microsoft.com/v1.0/users/{REMETENTE}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    data_corte_iso = _data_corte_odata()
    mensagens: List[Dict[str, Any]] = []
    vistos: Set[str] = set()

    for assunto in ASSUNTOS_NAO_ENTREGA:
        params = {
            "$top": BOUNCE_PAGE_SIZE,
            "$filter": (
                f"receivedDateTime ge {data_corte_iso} "
                f"and contains(subject,'{_odata_string(assunto)}')"
            ),
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,receivedDateTime,bodyPreview,body",
        }

        try:
            resultados = _paged_request(base_url, headers, params)
        except requests.RequestException as exc:
            print(f"Consulta Outlook por assunto '{assunto}' falhou: {exc}")
            continue

        for msg in resultados:
            chave = msg.get("id") or f"{msg.get('subject', '')}|{msg.get('receivedDateTime', '')}"
            if chave in vistos:
                continue
            vistos.add(chave)
            mensagens.append(msg)

    return mensagens[:BOUNCE_MAX_MESSAGES]


def _limpar_texto_email(text: str) -> str:
    raw_text = (text or "").replace("=\r\n", "").replace("=\n", "")
    raw_text = re.sub(r"<br\s*/?>", "\n", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"</(p|div|li|tr|td|h[1-6])>", "\n", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"<[^>]+>", " ", raw_text)
    raw_text = html.unescape(raw_text).replace("\u00a0", " ")
    raw_text = re.sub(r"[ \t]+", " ", raw_text)
    raw_text = re.sub(r"\n\s+", "\n", raw_text)
    return raw_text.strip()


def _emails_no_texto(text: str) -> List[str]:
    emails: List[str] = []
    vistos: Set[str] = set()
    for match in EMAIL_PATTERN.finditer(text or ""):
        email = _normalize_email(match.group(0).strip(".,;:<>[]()"))
        if not email or email in vistos:
            continue
        vistos.add(email)
        emails.append(email)
    return emails


def _extract_recipient(text: str, destinatarios_alvo: Optional[Iterable[str]] = None) -> str:
    texto_limpo = _limpar_texto_email(text)
    emails_no_corpo = set(_emails_no_texto(texto_limpo))
    alvos = [_normalize_email(email) for email in (destinatarios_alvo or []) if _normalize_email(email)]

    for alvo in alvos:
        if alvo in emails_no_corpo:
            return alvo

    return DESTINATARIO_DESCONHECIDO


def buscar_bounces_outlook(destinatarios_alvo: Optional[Iterable[str]] = None) -> List[Dict[str, str]]:
    auth = _build_client()
    token = auth.get_token()
    messages = _list_messages(token)

    bounces = []
    for msg in messages:
        body_html = msg.get("body", {}).get("content", "") or ""
        preview = msg.get("bodyPreview", "") or ""
        texto = body_html if body_html else preview
        destinatario = _extract_recipient(texto, destinatarios_alvo)
        if destinatario == DESTINATARIO_DESCONHECIDO:
            continue

        bounces.append(
            {
                "Destinatario": destinatario,
                "Motivo do bounce": "Retorno de não entrega encontrado no Outlook",
                "Recebido em": msg.get("receivedDateTime", ""),
            }
        )

    print(
        f"Mensagens com assunto de não entrega analisadas: {len(messages)} | "
        f"Retornos com destinatário do relatório: {len(bounces)}"
    )
    return bounces
