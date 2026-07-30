import base64
import logging
import re
import time
from email.message import EmailMessage

from googleapiclient.errors import HttpError

from services.email_template import renderizar_template_email
from services.pdf_files import localizar_pdfs, nome_anexo


logger = logging.getLogger(__name__)


class GmailEmailService:
    def __init__(
        self,
        service,
        remetente: str,
        cartas_dir: str,
        rate_limit: int = 120,
        rate_limit_window_seconds: int = 60,
        retries: int = 3,
        retry_delay_seconds: float = 5.0,
    ) -> None:
        if rate_limit < 1:
            raise ValueError("rate_limit deve ser maior que zero.")
        if rate_limit_window_seconds < 1:
            raise ValueError("rate_limit_window_seconds deve ser maior que zero.")
        if retries < 1:
            raise ValueError("retries deve ser maior que zero.")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds não pode ser negativo.")

        self.service = service
        self.remetente = remetente.strip()
        self.cartas_dir = cartas_dir
        self.rate_limit = rate_limit
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self._requests_in_window = 0
        self._window_start = time.monotonic()

    def enviar_emails_em_massa(
        self,
        lista_credores,
        assunto: str,
        template: str,
    ) -> list[dict[str, str]]:
        resultados = []
        for credor in lista_credores:
            try:
                raw_message = self._criar_mensagem(credor, assunto, template)
                status, erro = self._enviar_mensagem_com_tentativas(raw_message)
            except Exception as exc:
                logger.exception("Falha ao preparar e-mail para %s", credor.email)
                status, erro = "Falha", str(exc)

            resultados.append(
                {
                    "Destinatario": credor.email,
                    "Status do envio": status,
                    "Erro": erro,
                }
            )
        return resultados

    def _criar_mensagem(self, credor, assunto: str, template: str) -> str:
        destinatario = re.sub(
            r"\s+",
            "",
            str(credor.email or "").replace("\u00a0", ""),
        )
        if not destinatario:
            raise ValueError(f"E-mail vazio para {credor.nome}.")

        pdf_paths = localizar_pdfs(self.cartas_dir, credor)
        if not pdf_paths:
            raise FileNotFoundError(f"PDF obrigatório ausente para {credor.nome}.")

        message = EmailMessage()
        message["To"] = destinatario
        message["From"] = self.remetente
        message["Subject"] = assunto
        message.set_content(
            f"Prezado(a) {credor.nome}, segue comunicado importante em anexo."
        )
        message.add_alternative(
            renderizar_template_email(template, credor),
            subtype="html",
        )

        for index, pdf_path in enumerate(pdf_paths):
            pdf_data = pdf_path.read_bytes()
            if not pdf_data:
                raise ValueError(f"PDF vazio: {pdf_path.name}.")
            message.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=nome_anexo(credor, index),
            )

        return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")

    def _enviar_mensagem_com_tentativas(
        self,
        raw_message: str,
    ) -> tuple[str, str]:
        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            try:
                (
                    self.service.users()
                    .messages()
                    .send(userId="me", body={"raw": raw_message})
                    .execute()
                )
                self._requests_in_window += 1
                return "Enviado", "N/A"
            except HttpError as exc:
                self._requests_in_window += 1
                status_code = getattr(exc.resp, "status", None)
                retryable = status_code == 429 or (
                    status_code is not None and status_code >= 500
                )
                if attempt < self.retries and retryable:
                    time.sleep(self.retry_delay_seconds)
                    continue
                return "Falha", f"Erro HTTP Gmail: {exc}"

        return "Falha", "Limite de tentativas atingido."

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._window_start
        if elapsed >= self.rate_limit_window_seconds:
            self._window_start = now
            self._requests_in_window = 0
            return

        if self._requests_in_window < self.rate_limit:
            return

        wait = self.rate_limit_window_seconds - elapsed
        if wait > 0:
            time.sleep(wait)
        self._window_start = time.monotonic()
        self._requests_in_window = 0
