import base64
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from util.input_excel import gerar_nomes_candidatos_carta


class GraphEmailService:
    def __init__(self, token_provider, remetente: str, rate_limit_per_min: int = 30, retries: int = 3, cartas_dir: Optional[str] = None, require_pdf: bool = True):
        self.token_provider = token_provider
        self.remetente = remetente
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

    def enviar_emails_em_massa(self, lista_credores, assunto: str, template: str, imagem_path: str) -> List[Dict[str, Any]]:
        logs_envio = []
        for credor in lista_credores:
            status, erro = self._enviar_para_credor(credor, assunto, template, imagem_path)
            logs_envio.append({'Destinatario': credor.email, 'Status do envio': status, 'Erro': erro})
            logging.info(f"Email para {credor.email} - Status: {status} - Erro: {erro}")
        return logs_envio

    def _enviar_para_credor(self, credor, assunto: str, template: str, imagem_path: str) -> Tuple[str, str]:
        payload = self._build_payload(credor, assunto, template, imagem_path)
        if payload is None:
            return "Falha", "Erro ao montar payload"
        try:
            resp_status, resp_err = self._post_with_retries(payload)
            return resp_status, resp_err
        except Exception as exc:  # pragma: no cover - proteção geral
            return "Falha", str(exc)

    def _build_payload(self, credor, assunto: str, template: str, imagem_path: str) -> Optional[Dict[str, Any]]:
        try:
            destinatario = re.sub(r"\s+", "", str(credor.email or "").replace("\u00a0", "")).strip()
            if not destinatario:
                logging.error("Email de destinatario vazio apos limpeza")
                return None

            valor_fmt = self._format_valor_brl(credor.valor)
            corpo_html = template.format(
                nome=credor.nome,
                classe=credor.classe,
                valor=valor_fmt,
                cpf_cnpj=credor.cpf_cnpj,
                endereco=credor.endereco,
                natureza=credor.natureza,
                origem=credor.origem,
            )

            attachments = self._try_attach_pdfs(credor)
            if not attachments and self.require_pdf:
                logging.error(f"PDF obrigatorio ausente para {credor.email}")
                return None

            message = {
                "subject": assunto,
                "body": {"contentType": "HTML", "content": corpo_html},
                "toRecipients": [{"emailAddress": {"address": destinatario}}],
                "attachments": attachments,
            }

            return {"message": message, "saveToSentItems": True}
        except Exception as exc:
            logging.error(f"Erro ao criar payload para {credor.email}: {exc}", exc_info=True)
            return None

    @staticmethod
    def _format_valor_brl(valor_raw: str) -> str:
        if not valor_raw:
            return ""
        txt = str(valor_raw).strip()
        # Se já tiver letras (ex.: USD 1,234.56 ou "Ilíquido"), não formatamos
        if any(ch.isalpha() for ch in txt):
            return txt
        dot_count = txt.count('.')
        comma_count = txt.count(',')

        def to_float(clean: str) -> Optional[float]:
            try:
                return float(clean)
            except ValueError:
                return None

        # Caso 1: possui vírgula => vírgula é decimal; pontos são milhar
        if comma_count:
            normalized = txt.replace('.', '').replace(',', '.')
            val = to_float(normalized)
        else:
            # Caso 2: só pontos. Se apenas um ponto e ele está nos últimos 3 chars, trate como decimal.
            if dot_count == 1 and txt.rfind('.') >= len(txt) - 3:
                val = to_float(txt)
            else:
                # Pontos como milhar; remove todos e trata como inteiro.
                normalized = txt.replace('.', '')
                val = to_float(normalized)

        if val is None:
            return txt

        formatted_en = f"{val:,.2f}"  # 1,234.56
        formatted_brl = formatted_en.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {formatted_brl}"

    def _build_pdf_attachment(self, credor, pdf_path: str, display_name: str) -> Optional[Dict[str, Any]]:
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
            if not pdf_bytes:
                logging.warning(f"Arquivo PDF vazio: {pdf_path}")
                return None
            return {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": display_name,
                "contentType": "application/pdf",
                "contentBytes": base64.b64encode(pdf_bytes).decode(),
            }
        except Exception as exc:
            logging.error(f"Erro ao anexar PDF para {credor.email}: {exc}", exc_info=True)
            return None

    def _collect_pdf_paths_for_candidate(self, filename: str) -> List[str]:
        base_name, ext = os.path.splitext(filename)
        all_paths: List[str] = []

        primary = os.path.normpath(os.path.join(self.cartas_dir, filename))
        if os.path.exists(primary):
            all_paths.append(primary)

        idx = 2
        while True:
            extra_name = f"{base_name}_{idx}{ext}"
            extra_path = os.path.normpath(os.path.join(self.cartas_dir, extra_name))
            if not os.path.exists(extra_path):
                break
            all_paths.append(extra_path)
            idx += 1

        return all_paths

    def _try_attach_pdfs(self, credor) -> List[Dict[str, Any]]:
        if not self.cartas_dir:
            return []
        if not os.path.isdir(self.cartas_dir):
            logging.warning(f"Diretorio de cartas nao encontrado: {self.cartas_dir}")
            return []

        candidatos = gerar_nomes_candidatos_carta(credor.nome, credor.cpf_cnpj, credor.classe)
        attachments: List[Dict[str, Any]] = []
        anexados = set()

        for filename in candidatos:
            pdf_paths = self._collect_pdf_paths_for_candidate(filename)
            if not pdf_paths:
                continue

            for idx, pdf_path in enumerate(pdf_paths, start=1):
                if pdf_path in anexados:
                    continue
                if idx == 1:
                    display_name = f"Comunicado - {credor.nome}.pdf"
                else:
                    display_name = f"Comunicado - {credor.nome} ({idx}).pdf"
                attachment = self._build_pdf_attachment(credor, pdf_path, display_name)
                if attachment:
                    attachments.append(attachment)
                    anexados.add(pdf_path)
            # Mantém o comportamento original: usa o primeiro padrão candidato encontrado,
            # mas agora com todos os seus sufixos (_2, _3, ...).
            if attachments:
                break

        if not attachments:
            logging.error(f"Nenhum PDF encontrado para {credor.nome} nos candidatos: {candidatos}")
        else:
            logging.info(f"Total de PDFs anexados para {credor.email}: {len(attachments)}")
        return attachments

    def _post_with_retries(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        url = f"https://graph.microsoft.com/v1.0/users/{self.remetente}/sendMail"

        for attempt in range(1, self.retries + 1):
            self._respect_rate_limit()
            token = self.token_provider.get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 202:
                self._sent_in_window += 1
                return "Enviado", "N/A"

            if response.status_code in (429, 503, 504) and attempt < self.retries:
                retry_after = int(response.headers.get('Retry-After', '5'))
                logging.warning(
                    f"Tentativa {attempt} falhou com {response.status_code}; aguardando {retry_after}s para nova tentativa"
                )
                time.sleep(retry_after)
                continue

            erro_trunc = response.text[:500]
            logging.error(
                f"Falha ao enviar email: status={response.status_code}, body={erro_trunc}, request-id={response.headers.get('request-id')}"
            )
            return "Falha", f"{response.status_code}: {erro_trunc}"

        return "Falha", "Limite de tentativas atingido"

    def _respect_rate_limit(self):
        now = time.time()
        elapsed = now - self._window_start
        if elapsed >= 60:
            self._window_start = now
            self._sent_in_window = 0
        if self._sent_in_window >= self.rate_limit_per_min:
            sleep_for = 60 - elapsed if elapsed < 60 else 0
            if sleep_for > 0:
                logging.info(f"Aguardando {sleep_for:.2f}s para respeitar o limite por minuto")
                time.sleep(sleep_for)
            self._window_start = time.time()
            self._sent_in_window = 0
