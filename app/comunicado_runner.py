import logging
from pathlib import Path
from typing import Callable

from app.comunicado_config import ComunicadoConfig
from config import (
    ARQUIVO_LOG,
    CLIENT_ID,
    CLIENT_SECRET,
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_REQUIRE_AUTH,
    SMTP_SECURITY,
    SMTP_USERNAME,
    TENANT_ID,
)
from services.auth import Auth
from services.gmail_email import GmailEmailService
from services.graph_auth import GraphAuth
from services.graph_email import GraphEmailService
from services.relatorio import Relatorio
from services.smtp_email import SmtpEmailService
from util.input_excel import carregar_credores


def _validar_arquivos(configuracao: ComunicadoConfig) -> None:
    arquivo_emails = Path(configuracao.arquivo_emails)
    if not arquivo_emails.is_file():
        raise FileNotFoundError(f"Planilha não encontrada: {arquivo_emails}")

    cartas_dir = Path(configuracao.cartas_dir)
    if not cartas_dir.is_dir():
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {cartas_dir}")


def _exigir_variaveis(provider: str, variaveis: dict[str, str]) -> None:
    ausentes = [nome for nome, valor in variaveis.items() if not str(valor).strip()]
    if ausentes:
        raise ValueError(
            f"Configuração incompleta para {provider}: {', '.join(ausentes)}."
        )


def _executar_outlook(
    configuracao: ComunicadoConfig,
    lista_credores,
):
    _exigir_variaveis(
        "outlook",
        {
            "GRAPH_TENANT_ID": TENANT_ID,
            "GRAPH_CLIENT_ID": CLIENT_ID,
            "GRAPH_CLIENT_SECRET": CLIENT_SECRET,
        },
    )
    auth = GraphAuth(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    email_service = GraphEmailService(
        token_provider=auth,
        remetente=configuracao.remetente,
        rate_limit_per_min=configuracao.rate_limit,
        retries=configuracao.retries,
        cartas_dir=configuracao.cartas_dir,
        request_timeout_seconds=configuracao.timeout_seconds,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
    )


def _executar_gmail(
    configuracao: ComunicadoConfig,
    lista_credores,
):
    token_path = Path(GMAIL_TOKEN_FILE)
    credentials_path = Path(GMAIL_CREDENTIALS_FILE)
    if not token_path.is_file() and not credentials_path.is_file():
        raise FileNotFoundError(
            "Gmail requer GMAIL_TOKEN_FILE ou GMAIL_CREDENTIALS_FILE válido."
        )

    service = Auth(
        token_path=str(token_path),
        credentials_path=str(credentials_path),
    ).get_service()
    email_service = GmailEmailService(
        service=service,
        remetente=configuracao.remetente,
        cartas_dir=configuracao.cartas_dir,
        rate_limit=configuracao.rate_limit,
        rate_limit_window_seconds=configuracao.rate_limit_window_seconds,
        retries=configuracao.retries,
        retry_delay_seconds=configuracao.retry_delay_seconds,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
    )


def _executar_smtp(
    configuracao: ComunicadoConfig,
    lista_credores,
):
    email_service = SmtpEmailService(
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        remetente=configuracao.remetente,
        security_mode=SMTP_SECURITY,
        timeout=configuracao.timeout_seconds,
        require_auth=SMTP_REQUIRE_AUTH,
        rate_limit=configuracao.rate_limit,
        rate_limit_window_seconds=configuracao.rate_limit_window_seconds,
        retries=configuracao.retries,
        retry_delay_seconds=configuracao.retry_delay_seconds,
        cartas_dir=configuracao.cartas_dir,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
    )


RUNNERS: dict[str, Callable] = {
    "outlook": _executar_outlook,
    "gmail": _executar_gmail,
    "smtp": _executar_smtp,
}


def executar_comunicado(configuracao: ComunicadoConfig) -> None:
    logging.basicConfig(
        filename=ARQUIVO_LOG,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    _validar_arquivos(configuracao)
    lista_credores = carregar_credores(configuracao.arquivo_emails)
    print(
        f"Iniciando envio via {configuracao.provider} para "
        f"{len(lista_credores)} credores..."
    )

    logs_envio = RUNNERS[configuracao.provider](configuracao, lista_credores)
    Relatorio(configuracao.arquivo_relatorio).gerar_relatorio(logs_envio)
    print("Envio de e-mails concluído.")
