import logging
import mimetypes
import os
import re
import smtplib
import ssl
import time
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from services.email_template import renderizar_template_email
from util.input_excel import gerar_nomes_candidatos_carta


class SmtpEmailService:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        remetente: str,
        security_mode: str = "auto",
        timeout: int = 60,
        require_auth: bool = True,
        rate_limit_per_min: int = 120,
        rate_limit_window_seconds: int = 60,
        retries: int = 3,
        cartas_dir: Optional[str] = None,
        require_pdf: bool = True,
    ):
        self.smtp_host = (smtp_host or "").strip()
        self.smtp_port = int(smtp_port)
        self.username = (username or "").strip()
        self.password = password or ""
        self.remetente = remetente
        self.security_mode = (security_mode or "auto").strip().lower()
        self.timeout = int(timeout)
        self.require_auth = require_auth
        self.rate_limit_per_min = rate_limit_per_min
        self.rate_limit_window_seconds = int(rate_limit_window_seconds)
        self.retries = retries
        self.cartas_dir = cartas_dir
        self.require_pdf = require_pdf
        self._sent_in_window = 0
        self._window_start = time.time()

        logging.basicConfig(
            filename="email_log.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def enviar_emails_em_massa(
        self,
        lista_credores,
        assunto: str,
        template: str,
        imagem_path: str,
    ) -> List[Dict[str, Any]]:
        logs_envio = []
        for credor in lista_credores:
            status, erro = self._enviar_para_credor(
                credor,
                assunto,
                template,
                imagem_path,
            )
            logs_envio.append(
                {
                    "Destinatario": credor.email,
                    "Status do envio": status,
                    "Erro": erro,
                }
            )
            logging.info(
                f"Email para {credor.email} - Status: {status} - Erro: {erro}"
            )
        return logs_envio

    def _enviar_para_credor(
        self,
        credor,
        assunto: str,
        template: str,
        imagem_path: str,
    ) -> Tuple[str, str]:
        destinatario, message = self._build_message(
            credor,
            assunto,
            template,
            imagem_path,
        )
        if message is None or not destinatario:
            return "Falha", "Erro ao montar mensagem"
        return self._send_with_retries(destinatario, message)

    def _build_message(
        self,
        credor,
        assunto: str,
        template: str,
        imagem_path: str,
    ) -> Tuple[str, Optional[MIMEMultipart]]:
        try:
            destinatario = re.sub(
                r"\s+",
                "",
                str(credor.email or "").replace("\u00a0", ""),
            ).strip()
            if not destinatario:
                logging.error(f"Email vazio para {credor.nome}")
                return "", None

            corpo_html = renderizar_template_email(template, credor)

            message = MIMEMultipart("mixed")
            message["From"] = self.remetente
            message["To"] = destinatario
            message["Subject"] = assunto

            related = MIMEMultipart("related")
            alternative = MIMEMultipart("alternative")
            texto_plano = (
                f"Prezado(a) {credor.nome}, segue comunicado importante em anexo."
                if self.require_pdf
                else f"Prezado(a) {credor.nome}, segue comunicado importante no corpo deste email."
            )
            alternative.attach(
                MIMEText(
                    texto_plano,
                    "plain",
                    "utf-8",
                )
            )
            alternative.attach(MIMEText(corpo_html, "html", "utf-8"))
            related.attach(alternative)

            self._attach_inline_image(related, imagem_path)
            message.attach(related)

            anexos = self._find_pdf_paths(credor)
            if not anexos and self.require_pdf:
                raise FileNotFoundError(f"PDF obrigatorio ausente para {credor.nome}")

            for idx, pdf_path in enumerate(anexos):
                with open(pdf_path, "rb") as pdf_file:
                    part = MIMEApplication(pdf_file.read(), _subtype="pdf")
                if idx == 0:
                    filename = f"Comunicado - {credor.nome}.pdf"
                else:
                    filename = f"Comunicado - {credor.nome} ({idx + 1}).pdf"
                part.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(part)

            return destinatario, message
        except Exception as exc:
            logging.error(
                f"Erro ao criar mensagem para {credor.email}: {exc}",
                exc_info=True,
            )
            return "", None

    def _attach_inline_image(self, related_message: MIMEMultipart, imagem_path: str) -> None:
        imagem_path = (imagem_path or "").strip()
        if not imagem_path:
            return

        imagem_path_norm = os.path.normpath(imagem_path)
        if not os.path.exists(imagem_path_norm):
            logging.warning(f"Imagem inline nao encontrada: {imagem_path_norm}")
            return

        content_type, _ = mimetypes.guess_type(imagem_path_norm)
        if not content_type:
            content_type = "image/png"
        maintype, subtype = content_type.split("/", 1)

        with open(imagem_path_norm, "rb") as img_file:
            image_part = MIMEBase(maintype, subtype)
            image_part.set_payload(img_file.read())

        encoders.encode_base64(image_part)
        image_part.add_header("Content-ID", "<imagem1>")
        image_part.add_header(
            "Content-Disposition",
            "inline",
            filename=os.path.basename(imagem_path_norm),
        )
        related_message.attach(image_part)

    def _find_pdf_paths(self, credor) -> List[str]:
        if not self.cartas_dir:
            return []
        if not os.path.isdir(self.cartas_dir):
            logging.warning(f"Diretorio de cartas nao encontrado: {self.cartas_dir}")
            return []

        candidatos = gerar_nomes_candidatos_carta(
            credor.nome,
            credor.cpf_cnpj,
            credor.classe,
        )
        for filename in candidatos:
            path = os.path.normpath(os.path.join(self.cartas_dir, filename))
            if not os.path.exists(path):
                continue

            base_name, ext = os.path.splitext(filename)
            encontrados = [path]
            i = 2
            while True:
                extra = os.path.normpath(
                    os.path.join(self.cartas_dir, f"{base_name}_{i}{ext}")
                )
                if not os.path.exists(extra):
                    break
                encontrados.append(extra)
                i += 1
            return encontrados

        logging.error(
            f"Nenhum PDF encontrado para {credor.nome} nos candidatos: {candidatos}"
        )
        return []

    def _send_with_retries(
        self,
        destinatario: str,
        message: MIMEMultipart,
    ) -> Tuple[str, str]:
        valid_modes = {"auto", "none", "starttls", "ssl"}
        if self.security_mode not in valid_modes:
            return (
                "Falha",
                "SMTP_SECURITY invalido. Use auto, none, starttls ou ssl.",
            )
        if not self.smtp_host:
            return "Falha", "SMTP_HOST nao configurado"
        if self.require_auth and not self.username:
            return "Falha", "SMTP_USERNAME nao configurado"
        if self.require_auth and not self.password:
            return "Falha", "SMTP_PASSWORD nao configurado"

        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            try:
                with self._connect() as client:
                    client.send_message(message, from_addr=self.remetente, to_addrs=[destinatario])
                self._sent_in_window += 1
                return "Enviado", "N/A"
            except smtplib.SMTPResponseException as exc:
                erro = f"{exc.smtp_code}: {self._decode_smtp_error(exc.smtp_error)}"
                logging.warning(
                    f"Tentativa {attempt} falhou no SMTP para {destinatario} - {erro}"
                )
                if attempt < self.retries and exc.smtp_code in {421, 450, 451, 452}:
                    time.sleep(5)
                    continue
                return "Falha", erro
            except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
                erro = str(exc)
                logging.warning(
                    f"Tentativa {attempt} falhou no SMTP para {destinatario} - {erro}"
                )
                if attempt < self.retries:
                    time.sleep(5)
                    continue
                return "Falha", erro

        return "Falha", "Limite de tentativas atingido"

    def _connect(self):
        if self.security_mode == "auto":
            try:
                return self._connect_with_mode("starttls")
            except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
                logging.warning(
                    "Falha ao iniciar STARTTLS no modo auto; retomando sem criptografia. "
                    f"Erro: {exc}"
                )
                return self._connect_with_mode("none")
        return self._connect_with_mode(self.security_mode)

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

    def _respect_rate_limit(self):
        now = time.time()
        elapsed = now - self._window_start
        window_seconds = max(1, self.rate_limit_window_seconds)
        if elapsed >= window_seconds:
            self._window_start = now
            self._sent_in_window = 0
        if self._sent_in_window >= self.rate_limit_per_min:
            wait = window_seconds - elapsed if elapsed < window_seconds else 0
            if wait > 0:
                time.sleep(wait)
            self._window_start = time.time()
            self._sent_in_window = 0
