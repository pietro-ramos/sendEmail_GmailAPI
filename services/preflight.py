from __future__ import annotations

import base64
import binascii
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import Any, Iterable

from services.pdf_files import localizar_pdfs
from util.input_excel import gerar_nomes_candidatos_carta


_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


@dataclass
class ResultadoPreflight:
    linha_planilha: int
    nome: str
    destinatario: str
    anexos: list[str] = field(default_factory=list)
    tamanho_payload_bytes: int = 0
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def aprovado(self) -> bool:
        return not self.erros


def normalizar_endereco_email(value: str) -> str:
    return re.sub(
        r"\s+",
        "",
        str(value or "").replace("\u00a0", ""),
    )


def validar_endereco_email(value: str, campo: str = "Destinatário") -> list[str]:
    endereco = normalizar_endereco_email(value)
    if not endereco:
        return [f"{campo} vazio."]
    if "," in endereco or ";" in endereco:
        return [
            f"{campo} contém mais de um endereço; cada linha deve ter somente um."
        ]
    if len(endereco) > 254:
        return [f"{campo} excede 254 caracteres."]
    if not endereco.isascii():
        return [f"{campo} contém caracteres não ASCII não suportados pelo fluxo."]
    if not _EMAIL_PATTERN.fullmatch(endereco):
        return [f"{campo} possui formato inválido: {endereco!r}."]

    local, domain = endereco.rsplit("@", 1)
    if len(local) > 64:
        return [f"{campo} possui parte local maior que 64 caracteres."]
    if len(domain) > 253:
        return [f"{campo} possui domínio maior que 253 caracteres."]
    if domain.rsplit(".", 1)[-1].isdigit():
        return [f"{campo} possui domínio sem sufixo textual válido."]
    return []


def _adicionar_unicos(destino: list[str], novos: Iterable[str]) -> None:
    for item in novos:
        if item and item not in destino:
            destino.append(item)


def _texto_obrigatorio(
    mapping: dict[str, Any],
    key: str,
    descricao: str,
    erros: list[str],
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        erros.append(f"Payload sem {descricao}.")
        return ""
    return value


def validar_payload_graph(
    payload: Any,
) -> tuple[list[str], list[str]]:
    erros: list[str] = []
    avisos: list[str] = []
    if not isinstance(payload, dict):
        return ["Payload Graph não é um objeto JSON."], avisos

    message = payload.get("message")
    if not isinstance(message, dict):
        return ["Payload Graph sem o objeto 'message'."], avisos

    _texto_obrigatorio(message, "subject", "assunto", erros)

    body = message.get("body")
    if not isinstance(body, dict):
        erros.append("Payload Graph sem corpo da mensagem.")
    else:
        content_type = body.get("contentType")
        if content_type not in {"HTML", "Text"}:
            erros.append("Payload Graph com contentType inválido.")
        _texto_obrigatorio(body, "content", "conteúdo do corpo", erros)

    recipients = message.get("toRecipients")
    if not isinstance(recipients, list) or not recipients:
        erros.append("Payload Graph sem destinatário.")
    else:
        for index, recipient in enumerate(recipients, start=1):
            if not isinstance(recipient, dict):
                erros.append(f"Destinatário Graph #{index} possui estrutura inválida.")
                continue
            email_address = recipient.get("emailAddress")
            if not isinstance(email_address, dict):
                erros.append(
                    f"Destinatário Graph #{index} não possui 'emailAddress'."
                )
                continue
            _adicionar_unicos(
                erros,
                validar_endereco_email(
                    email_address.get("address", ""),
                    campo=f"Destinatário Graph #{index}",
                ),
            )

    attachments = message.get("attachments")
    if not isinstance(attachments, list) or not attachments:
        erros.append("Payload Graph sem anexo PDF.")
    else:
        for index, attachment in enumerate(attachments, start=1):
            if not isinstance(attachment, dict):
                erros.append(f"Anexo Graph #{index} possui estrutura inválida.")
                continue
            _texto_obrigatorio(
                attachment,
                "name",
                f"nome do anexo #{index}",
                erros,
            )
            if attachment.get("contentType") != "application/pdf":
                erros.append(f"Anexo Graph #{index} não está marcado como PDF.")
            if (
                attachment.get("@odata.type")
                != "#microsoft.graph.fileAttachment"
            ):
                erros.append(f"Anexo Graph #{index} sem tipo fileAttachment.")

            encoded = attachment.get("contentBytes")
            if not isinstance(encoded, str) or not encoded:
                erros.append(f"Anexo Graph #{index} sem conteúdo.")
                continue
            try:
                decoded = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError):
                erros.append(f"Anexo Graph #{index} possui base64 inválido.")
                continue
            if not decoded:
                erros.append(f"Anexo Graph #{index} está vazio.")
            elif not decoded.startswith(b"%PDF-"):
                erros.append(f"Anexo Graph #{index} não possui assinatura PDF.")

    if not isinstance(payload.get("saveToSentItems"), bool):
        erros.append("Payload Graph sem 'saveToSentItems' booleano.")

    return erros, avisos


def validar_mensagem_mime(
    message: EmailMessage,
) -> tuple[list[str], list[str]]:
    erros: list[str] = []
    avisos: list[str] = []
    if not isinstance(message, EmailMessage):
        return ["Mensagem MIME possui estrutura inválida."], avisos

    _adicionar_unicos(
        erros,
        validar_endereco_email(str(message.get("From", "")), campo="Remetente"),
    )
    _adicionar_unicos(
        erros,
        validar_endereco_email(
            str(message.get("To", "")),
            campo="Destinatário MIME",
        ),
    )
    if not str(message.get("Subject", "")).strip():
        erros.append("Mensagem MIME sem assunto.")

    html_part = message.get_body(preferencelist=("html",))
    if html_part is None:
        erros.append("Mensagem MIME sem corpo HTML.")
    else:
        html_content = html_part.get_content()
        if not isinstance(html_content, str) or not html_content.strip():
            erros.append("Mensagem MIME com corpo HTML vazio.")

    attachments = list(message.iter_attachments())
    if not attachments:
        erros.append("Mensagem MIME sem anexo PDF.")
    for index, attachment in enumerate(attachments, start=1):
        if attachment.get_content_type() != "application/pdf":
            erros.append(f"Anexo MIME #{index} não está marcado como PDF.")
        if not attachment.get_filename():
            erros.append(f"Anexo MIME #{index} não possui nome.")
        content = attachment.get_payload(decode=True)
        if not content:
            erros.append(f"Anexo MIME #{index} está vazio.")
        elif not content.startswith(b"%PDF-"):
            erros.append(f"Anexo MIME #{index} não possui assinatura PDF.")

    return erros, avisos


def validar_payload_gmail(
    payload: Any,
) -> tuple[list[str], list[str], EmailMessage | None]:
    erros: list[str] = []
    avisos: list[str] = []
    if not isinstance(payload, dict):
        return ["Payload Gmail não é um objeto."], avisos, None

    raw = payload.get("raw")
    if not isinstance(raw, str) or not raw:
        return ["Payload Gmail sem a mensagem em 'raw'."], avisos, None
    try:
        decoded = base64.urlsafe_b64decode(raw)
        message = BytesParser(policy=policy.default).parsebytes(decoded)
    except (ValueError, binascii.Error) as exc:
        return [f"Payload Gmail possui base64 inválido: {exc}"], avisos, None

    mime_errors, mime_warnings = validar_mensagem_mime(message)
    _adicionar_unicos(erros, mime_errors)
    _adicionar_unicos(avisos, mime_warnings)
    return erros, avisos, message


class PreflightService:
    def __init__(
        self,
        provider: str,
        email_service,
        remetente: str,
    ) -> None:
        if provider not in {"outlook", "gmail", "smtp"}:
            raise ValueError("Provedor inválido para o preflight.")
        self.provider = provider
        self.email_service = email_service
        self.remetente = remetente

    def executar(
        self,
        lista_credores,
        assunto: str,
        template: str,
    ) -> list[ResultadoPreflight]:
        resultados = [
            self._validar_credor(
                credor,
                linha_planilha=linha_planilha,
                assunto=assunto,
                template=template,
            )
            for linha_planilha, credor in enumerate(lista_credores, start=2)
        ]
        self._avisar_destinatarios_repetidos(resultados)
        return resultados

    def _validar_credor(
        self,
        credor,
        linha_planilha: int,
        assunto: str,
        template: str,
    ) -> ResultadoPreflight:
        resultado = ResultadoPreflight(
            linha_planilha=linha_planilha,
            nome=str(credor.nome or ""),
            destinatario=normalizar_endereco_email(credor.email),
        )
        if not resultado.nome.strip():
            resultado.erros.append("Nome do credor vazio.")
        if not str(credor.cpf_cnpj or "").strip():
            resultado.erros.append("CPF/CNPJ vazio.")
        _adicionar_unicos(
            resultado.erros,
            validar_endereco_email(resultado.destinatario),
        )
        if not str(self.remetente or "").strip():
            resultado.erros.append("Remetente vazio.")
        elif self.provider != "outlook":
            _adicionar_unicos(
                resultado.erros,
                validar_endereco_email(self.remetente, campo="Remetente"),
            )
        if not str(assunto or "").strip():
            resultado.erros.append("Assunto vazio.")
        if not str(template or "").strip():
            resultado.erros.append("Template vazio.")

        pdf_paths = localizar_pdfs(self.email_service.cartas_dir, credor)
        resultado.anexos = [path.name for path in pdf_paths]
        if not pdf_paths:
            candidatos = gerar_nomes_candidatos_carta(
                credor.nome,
                credor.cpf_cnpj,
                credor.classe,
            )
            candidatos_texto = ", ".join(candidatos) or "(nenhum)"
            resultado.erros.append(
                "PDF obrigatório não localizado. "
                f"Candidatos-base: {candidatos_texto}; "
                "sufixos _2, _3 e seguintes também foram verificados."
            )
            return resultado

        for pdf_path in pdf_paths:
            try:
                pdf_data = pdf_path.read_bytes()
            except OSError as exc:
                resultado.erros.append(
                    f"Não foi possível ler {pdf_path.name}: {exc}."
                )
                continue
            if not pdf_data:
                resultado.erros.append(f"PDF vazio: {pdf_path.name}.")
            elif not pdf_data.startswith(b"%PDF-"):
                resultado.erros.append(
                    f"Arquivo sem assinatura PDF: {pdf_path.name}."
                )

        try:
            self._montar_e_validar_payload(
                credor,
                assunto,
                template,
                resultado,
            )
        except Exception as exc:
            resultado.erros.append(
                f"Falha ao montar o payload {self.provider}: "
                f"{type(exc).__name__}: {exc}"
            )
        return resultado

    def _montar_e_validar_payload(
        self,
        credor,
        assunto: str,
        template: str,
        resultado: ResultadoPreflight,
    ) -> None:
        if self.provider == "outlook":
            payload = self.email_service._build_payload(
                credor,
                assunto,
                template,
            )
            if payload is None:
                resultado.erros.append(
                    "O construtor do Outlook não conseguiu gerar o payload."
                )
                return
            erros, avisos = validar_payload_graph(payload)
            resultado.tamanho_payload_bytes = len(
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
        elif self.provider == "gmail":
            raw = self.email_service._criar_mensagem(
                credor,
                assunto,
                template,
            )
            payload = {"raw": raw}
            erros, avisos, _ = validar_payload_gmail(payload)
            resultado.tamanho_payload_bytes = len(
                json.dumps(payload).encode("utf-8")
            )
        else:
            destinatario, message = self.email_service._build_message(
                credor,
                assunto,
                template,
            )
            if normalizar_endereco_email(destinatario) != resultado.destinatario:
                resultado.erros.append(
                    "Destinatário do payload SMTP diverge da planilha."
                )
            erros, avisos = validar_mensagem_mime(message)
            resultado.tamanho_payload_bytes = len(message.as_bytes())

        destinatario_ja_reprovado = any(
            erro.startswith("Destinatário possui")
            or erro.startswith("Destinatário vazio")
            or erro.startswith("Destinatário contém")
            or erro.startswith("Destinatário excede")
            for erro in resultado.erros
        )
        if destinatario_ja_reprovado:
            erros = [
                erro
                for erro in erros
                if not erro.startswith("Destinatário Graph #")
                and not erro.startswith("Destinatário MIME")
            ]
        _adicionar_unicos(resultado.erros, erros)
        _adicionar_unicos(resultado.avisos, avisos)

    @staticmethod
    def _avisar_destinatarios_repetidos(
        resultados: list[ResultadoPreflight],
    ) -> None:
        counts = Counter(
            resultado.destinatario.lower()
            for resultado in resultados
            if not validar_endereco_email(resultado.destinatario)
        )
        for resultado in resultados:
            count = counts.get(resultado.destinatario.lower(), 0)
            if count > 1:
                resultado.avisos.append(
                    f"Destinatário aparece em {count} linhas do lote."
                )
