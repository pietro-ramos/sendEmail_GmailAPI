import base64
import logging
import re
import time
from typing import Any

import requests

from services.email_template import renderizar_template_email
from services.pdf_files import localizar_pdfs, nome_anexo


logger = logging.getLogger(__name__)


class GraphEmailService:
    def __init__(
        self,
        token_provider,
        remetente: str,
        rate_limit_per_min: int = 30,
        retries: int = 3,
        cartas_dir: str = "data/cartas",
        request_timeout_seconds: float = 30.0,
    ) -> None:
        if rate_limit_per_min < 1:
            raise ValueError("rate_limit_per_min deve ser maior que zero.")
        if retries < 1:
            raise ValueError("retries deve ser maior que zero.")
        if request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds deve ser maior que zero.")

        self.token_provider = token_provider
        self.remetente = remetente.strip()
        self.rate_limit_per_min = rate_limit_per_min
        self.retries = retries
        self.cartas_dir = cartas_dir
        self.request_timeout_seconds = request_timeout_seconds
        self._sent_in_window = 0
        self._window_start = time.monotonic()

    def enviar_emails_em_massa(
        self,
        lista_credores,
        assunto: str,
        template: str,
    ) -> list[dict[str, str]]:
        resultados = []
        for credor in lista_credores:
            payload = self._build_payload(credor, assunto, template)
            if payload is None:
                status, erro = "Falha", "Erro ao montar mensagem ou localizar PDF."
            else:
                status, erro = self._post_with_retries(payload)

            resultados.append(
                {
                    "Destinatario": credor.email,
                    "Status do envio": status,
                    "Erro": erro,
                }
            )
        return resultados

    def _build_payload(
        self,
        credor,
        assunto: str,
        template: str,
    ) -> dict[str, Any] | None:
        try:
            destinatario = re.sub(
                r"\s+",
                "",
                str(credor.email or "").replace("\u00a0", ""),
            )
            if not destinatario:
                raise ValueError(f"E-mail vazio para {credor.nome}.")

            attachments = self._build_pdf_attachments(credor)
            if not attachments:
                raise FileNotFoundError(
                    f"PDF obrigatório ausente para {credor.nome}."
                )

            return {
                "message": {
                    "subject": assunto,
                    "body": {
                        "contentType": "HTML",
                        "content": renderizar_template_email(template, credor),
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": destinatario}}
                    ],
                    "attachments": attachments,
                },
                "saveToSentItems": True,
            }
        except Exception:
            logger.exception("Falha ao montar payload para %s", credor.email)
            return None

    def _build_pdf_attachments(self, credor) -> list[dict[str, str]]:
        attachments = []
        for index, pdf_path in enumerate(localizar_pdfs(self.cartas_dir, credor)):
            pdf_bytes = pdf_path.read_bytes()
            if not pdf_bytes:
                logger.warning("PDF vazio: %s", pdf_path)
                continue
            attachments.append(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": nome_anexo(credor, index),
                    "contentType": "application/pdf",
                    "contentBytes": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            )
        return attachments

    def _post_with_retries(
        self,
        payload: dict[str, Any],
    ) -> tuple[str, str]:
        url = f"https://graph.microsoft.com/v1.0/users/{self.remetente}/sendMail"

        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            headers = {
                "Authorization": f"Bearer {self.token_provider.get_token()}",
                "Content-Type": "application/json",
            }
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.request_timeout_seconds,
                )
            except requests.RequestException as exc:
                if attempt < self.retries:
                    time.sleep(5)
                    continue
                return "Falha", str(exc)

            if response.status_code == 202:
                self._sent_in_window += 1
                return "Enviado", "N/A"

            if response.status_code in {429, 503, 504} and attempt < self.retries:
                retry_after = self._retry_after_seconds(response)
                logger.warning(
                    "Tentativa %s falhou no Graph (%s); novo envio em %ss.",
                    attempt,
                    response.status_code,
                    retry_after,
                )
                time.sleep(retry_after)
                continue

            erro_truncado = response.text[:500]
            logger.error(
                "Falha Graph: status=%s request-id=%s body=%s",
                response.status_code,
                response.headers.get("request-id"),
                erro_truncado,
            )
            return "Falha", f"{response.status_code}: {erro_truncado}"

        return "Falha", "Limite de tentativas atingido."

    @staticmethod
    def _retry_after_seconds(response) -> int:
        try:
            return max(0, int(response.headers.get("Retry-After", "5")))
        except (TypeError, ValueError):
            return 5

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._window_start
        if elapsed >= 60:
            self._window_start = now
            self._sent_in_window = 0
            return

        if self._sent_in_window < self.rate_limit_per_min:
            return

        wait = 60 - elapsed
        if wait > 0:
            time.sleep(wait)
        self._window_start = time.monotonic()
        self._sent_in_window = 0
