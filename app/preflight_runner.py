from pathlib import Path

from app.comunicado_config import ComunicadoConfig
from config import (
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
from services.gmail_email import GmailEmailService
from services.graph_email import GraphEmailService
from services.preflight import PreflightService, ResultadoPreflight
from services.smtp_email import SmtpEmailService
from util.input_excel import carregar_credores


def _validar_entradas(configuracao: ComunicadoConfig) -> None:
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


def _montar_servico_sem_rede(configuracao: ComunicadoConfig):
    if configuracao.provider == "outlook":
        _exigir_variaveis(
            "outlook",
            {
                "GRAPH_TENANT_ID": TENANT_ID,
                "GRAPH_CLIENT_ID": CLIENT_ID,
                "GRAPH_CLIENT_SECRET": CLIENT_SECRET,
            },
        )
        return GraphEmailService(
            token_provider=None,
            remetente=configuracao.remetente,
            rate_limit_per_min=configuracao.rate_limit,
            retries=configuracao.retries,
            cartas_dir=configuracao.cartas_dir,
            request_timeout_seconds=configuracao.timeout_seconds,
        )

    if configuracao.provider == "gmail":
        token_path = Path(GMAIL_TOKEN_FILE)
        credentials_path = Path(GMAIL_CREDENTIALS_FILE)
        if not token_path.is_file() and not credentials_path.is_file():
            raise FileNotFoundError(
                "Gmail requer GMAIL_TOKEN_FILE ou "
                "GMAIL_CREDENTIALS_FILE válido."
            )
        return GmailEmailService(
            service=None,
            remetente=configuracao.remetente,
            cartas_dir=configuracao.cartas_dir,
            rate_limit=configuracao.rate_limit,
            rate_limit_window_seconds=configuracao.rate_limit_window_seconds,
            retries=configuracao.retries,
            retry_delay_seconds=configuracao.retry_delay_seconds,
        )

    return SmtpEmailService(
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


def executar_preflight(
    configuracao: ComunicadoConfig,
) -> list[ResultadoPreflight]:
    _validar_entradas(configuracao)
    lista_credores = carregar_credores(configuracao.arquivo_emails)
    email_service = _montar_servico_sem_rede(configuracao)
    return PreflightService(
        provider=configuracao.provider,
        email_service=email_service,
        remetente=configuracao.remetente,
    ).executar(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
    )
