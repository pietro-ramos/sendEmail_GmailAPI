import logging
import re
import smtplib
import ssl
import time
from email.message import EmailMessage

from services.email_template import renderizar_template_email
from services.pdf_files import localizar_pdfs, nome_anexo


logger = logging.getLogger(__name__)
TRANSIENT_SMTP_CODES = {421, 450, 451, 452}


class SmtpEmailService:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        remetente: str,
        security_mode: str = "starttls",
        timeout: float = 60.0,
        require_auth: bool = True,
        rate_limit: int = 40,
        rate_limit_window_seconds: int = 3600,
        retries: int = 3,
        retry_delay_seconds: float = 5.0,
        cartas_dir: str = "data/cartas",
    ) -> None:
        self.smtp_host = (smtp_host or "").strip()
        self.smtp_port = int(smtp_port)
        self.username = (username or "").strip()
        self.password = password or ""
        self.remetente = (remetente or "").strip()
        self.security_mode = (security_mode or "starttls").strip().lower()
        self.timeout = float(timeout)
        self.require_auth = require_auth
        self.rate_limit = int(rate_limit)
        self.rate_limit_window_seconds = int(rate_limit_window_seconds)
        self.retries = int(retries)
        self.retry_delay_seconds = float(retry_delay_seconds)
        self.cartas_dir = cartas_dir
        self._sent_in_window = 0
        self._window_start = time.monotonic()
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        if not self.smtp_host:
            raise ValueError("SMTP_HOST não configurado.")
        if not self.remetente:
            raise ValueError("EMAIL_REMETENTE_SMTP não configurado.")
        if self.smtp_port < 1:
            raise ValueError("SMTP_PORT deve ser maior que zero.")
        if self.security_mode not in {"auto", "none", "starttls", "ssl"}:
            raise ValueError(
                "SMTP_SECURITY inválido. Use auto, none, starttls ou ssl."
            )
        if self.require_auth and not self.username:
            raise ValueError("SMTP_USERNAME não configurado.")
        if self.require_auth and not self.password:
            raise ValueError("SMTP_PASSWORD não configurado.")
        if self.rate_limit < 1:
            raise ValueError("SMTP_RATE_LIMIT deve ser maior que zero.")
        if self.rate_limit_window_seconds < 1:
            raise ValueError("SMTP_RATE_WINDOW_SECONDS deve ser maior que zero.")
        if self.retries < 1:
            raise ValueError("SMTP_RETRIES deve ser maior que zero.")
        if self.retry_delay_seconds < 0:
            raise ValueError("SMTP_RETRY_DELAY_SECONDS não pode ser negativo.")
        if self.timeout <= 0:
            raise ValueError("SMTP_TIMEOUT deve ser maior que zero.")

    def enviar_emails_em_massa(
        self,
        lista_credores,
        assunto: str,
        template: str,
    ) -> list[dict[str, str]]:
        resultados = []
        for credor in lista_credores:
            try:
                destinatario, message = self._build_message(
                    credor,
                    assunto,
                    template,
                )
                status, erro = self._send_with_retries(destinatario, message)
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

    def _build_message(
        self,
        credor,
        assunto: str,
        template: str,
    ) -> tuple[str, EmailMessage]:
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
        message["From"] = self.remetente
        message["To"] = destinatario
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

        return destinatario, message

    def _send_with_retries(
        self,
        destinatario: str,
        message: EmailMessage,
    ) -> tuple[str, str]:
        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            try:
                with self._connect() as client:
                    client.send_message(
                        message,
                        from_addr=self.remetente,
                        to_addrs=[destinatario],
                    )
                self._sent_in_window += 1
                return "Enviado", "N/A"
            except smtplib.SMTPResponseException as exc:
                erro = (
                    f"{exc.smtp_code}: "
                    f"{self._decode_smtp_error(exc.smtp_error)}"
                )
                retryable = exc.smtp_code in TRANSIENT_SMTP_CODES
                if attempt < self.retries and retryable:
                    time.sleep(self.retry_delay_seconds)
                    continue
                return "Falha", erro
            except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
                if attempt < self.retries:
                    time.sleep(self.retry_delay_seconds)
                    continue
                return "Falha", str(exc)

        return "Falha", "Limite de tentativas atingido."

    def _connect(self):
        mode = self.security_mode
        if mode == "auto":
            mode = "ssl" if self.smtp_port == 465 else "starttls"
        return self._connect_with_mode(mode)

    def _connect_with_mode(self, mode: str):
        context = ssl.create_default_context()
        if mode == "ssl":
            client = smtplib.SMTP_SSL(
                self.smtp_host,
                self.smtp_port,
                timeout=self.timeout,
                context=context,
            )
        else:
            client = smtplib.SMTP(
                self.smtp_host,
                self.smtp_port,
                timeout=self.timeout,
            )
            client.ehlo()
            if mode == "starttls":
                client.starttls(context=context)
                client.ehlo()

        if self.require_auth:
            client.login(self.username, self.password)
        return client

    @staticmethod
    def _decode_smtp_error(raw_error: bytes) -> str:
        if isinstance(raw_error, bytes):
            return raw_error.decode("utf-8", errors="replace")
        return str(raw_error)

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._window_start
        if elapsed >= self.rate_limit_window_seconds:
            self._window_start = now
            self._sent_in_window = 0
            return

        if self._sent_in_window < self.rate_limit:
            return

        wait = self.rate_limit_window_seconds - elapsed
        if wait > 0:
            time.sleep(wait)
        self._window_start = time.monotonic()
        self._sent_in_window = 0
