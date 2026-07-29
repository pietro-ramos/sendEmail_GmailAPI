import logging
import os
import re
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

import requests

from util.input_excel import gerar_nomes_candidatos_carta


class LocawebEmailService:
    def __init__(
        self,
        api_token: str,
        remetente: str,
        api_url: str,
        rate_limit_per_min: int = 120,
        retries: int = 3,
        cartas_dir: Optional[str] = None,
        require_pdf: bool = True,
    ):
        self.api_token = (api_token or "").strip()
        self.remetente = remetente
        self.api_url = (api_url or "").strip()
        self.rate_limit_per_min = rate_limit_per_min
        self.retries = retries
        self.cartas_dir = cartas_dir
        self.require_pdf = require_pdf
        self._sent_in_window = 0
        self._window_start = time.time()

        logging.basicConfig(
            filename='email_log.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def enviar_emails_em_massa(self, lista_credores, assunto: str, template: str) -> List[Dict[str, Any]]:
        logs_envio = []
        for credor in lista_credores:
            status, erro = self._enviar_para_credor(credor, assunto, template)
            logs_envio.append({
                'Destinatario': credor.email,
                'Status do envio': status,
                'Erro': erro,
            })
            logging.info(f"Email para {credor.email} - Status: {status} - Erro: {erro}")
        return logs_envio

    def _enviar_para_credor(self, credor, assunto: str, template: str) -> Tuple[str, str]:
        payload = self._build_payload(credor, assunto, template)
        if payload is None:
            return "Falha", "Erro ao montar payload"
        return self._post_with_retries(payload)

    def _build_payload(self, credor, assunto: str, template: str) -> Optional[Dict[str, Any]]:
        try:
            destinatario = re.sub(r"\s+", "", str(credor.email or "").replace("\u00a0", "")).strip()
            if not destinatario:
                logging.error(f"Email vazio para {credor.nome}")
                return None

            corpo_html = template.format(
                nome=credor.nome,
                classe=credor.classe,
                valor=credor.valor,
                cpf_cnpj=credor.cpf_cnpj,
                endereco=credor.endereco,
                natureza=credor.natureza,
                origem=credor.origem,
            )

            plain_text = f"Prezado(a) {credor.nome}, segue comunicado importante em anexo."
            mime_body, content_type = self._build_mime_body(credor, plain_text, corpo_html)

            return {
                'subject': assunto,
                'from': self.remetente,
                'to': [destinatario],
                'headers': {
                    'Content-Type': content_type,
                    'x-source': 'sendEmail_GmailAPI-locaweb',
                },
                'body': mime_body,
            }
        except Exception as exc:
            logging.error(f"Erro ao criar payload para {credor.email}: {exc}", exc_info=True)
            return None

    def _build_mime_body(self, credor, plain_text: str, html_text: str) -> Tuple[str, str]:
        msg = MIMEMultipart('mixed')

        alt = MIMEMultipart('alternative')
        alt.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        alt.attach(MIMEText(html_text, 'html', 'utf-8'))
        msg.attach(alt)

        anexos = self._find_pdf_paths(credor)
        if not anexos and self.require_pdf:
            raise FileNotFoundError(f"PDF obrigatorio ausente para {credor.nome}")

        for idx, pdf_path in enumerate(anexos):
            with open(pdf_path, 'rb') as f:
                part = MIMEApplication(f.read(), _subtype='pdf')
            if idx == 0:
                filename = f"Comunicado - {credor.nome}.pdf"
            else:
                filename = f"Comunicado - {credor.nome} ({idx + 1}).pdf"
            part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(part)

        full_mime = msg.as_string()
        _, _, mime_body = full_mime.partition('\n\n')
        mime_body = mime_body.replace('\n', '\r\n')
        content_type = msg.get('Content-Type', 'multipart/mixed')
        return mime_body, content_type

    def _find_pdf_paths(self, credor) -> List[str]:
        if not self.cartas_dir:
            return []
        if not os.path.isdir(self.cartas_dir):
            logging.warning(f"Diretorio de cartas nao encontrado: {self.cartas_dir}")
            return []

        candidatos = gerar_nomes_candidatos_carta(credor.nome, credor.cpf_cnpj, credor.classe)
        for filename in candidatos:
            path = os.path.normpath(os.path.join(self.cartas_dir, filename))
            if not os.path.exists(path):
                continue
            base_name, ext = os.path.splitext(filename)
            encontrados = [path]
            i = 2
            while True:
                extra = os.path.normpath(os.path.join(self.cartas_dir, f"{base_name}_{i}{ext}"))
                if not os.path.exists(extra):
                    break
                encontrados.append(extra)
                i += 1
            return encontrados

        logging.error(f"Nenhum PDF encontrado para {credor.nome} nos candidatos: {candidatos}")
        return []

    def _post_with_retries(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        if not self.api_token:
            return 'Falha', 'LOCAWEB_API_TOKEN não configurado'
        if not self.api_url:
            return 'Falha', 'LOCAWEB_API_URL não configurado'

        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            headers = {
                'x-auth-token': self.api_token,
                'Content-Type': 'application/json',
            }
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)

            if response.status_code in (200, 201, 202):
                self._sent_in_window += 1
                return 'Enviado', 'N/A'

            if response.status_code in (429, 503, 504) and attempt < self.retries:
                retry_after = int(response.headers.get('Retry-After', '5'))
                time.sleep(max(retry_after, 1))
                continue

            erro_trunc = (response.text or '')[:500]
            logging.error(f"Falha Locaweb: status={response.status_code}, body={erro_trunc}")
            return 'Falha', f"{response.status_code}: {erro_trunc}"

        return 'Falha', 'Limite de tentativas atingido'

    def _respect_rate_limit(self):
        now = time.time()
        elapsed = now - self._window_start
        if elapsed >= 60:
            self._window_start = now
            self._sent_in_window = 0
        if self._sent_in_window >= self.rate_limit_per_min:
            wait = 60 - elapsed if elapsed < 60 else 0
            if wait > 0:
                time.sleep(wait)
            self._window_start = time.time()
            self._sent_in_window = 0
