from app import ComunicadoConfig, executar_comunicado
from config import (
    ARQUIVO_EMAILS,
    ARQUIVO_RELATORIO,
    ASSUNTO,
    CARTAS_DIR,
    GMAIL_RATE_LIMIT_PER_MINUTE,
    GMAIL_RETRIES,
    GMAIL_RETRY_DELAY_SECONDS,
    OUTLOOK_RATE_LIMIT_PER_MINUTE,
    OUTLOOK_REQUEST_TIMEOUT_SECONDS,
    OUTLOOK_RETRIES,
    PROVEDOR_ENVIO,
    REMETENTE,
    REMETENTE_GMAIL,
    REMETENTE_SMTP,
    SMTP_RATE_LIMIT,
    SMTP_RATE_WINDOW_SECONDS,
    SMTP_RETRIES,
    SMTP_RETRY_DELAY_SECONDS,
    SMTP_TIMEOUT,
    TEMPLATE_PDF,
)


PRESETS_POR_PROVEDOR = {
    "outlook": {
        "remetente": REMETENTE,
        "rate_limit": OUTLOOK_RATE_LIMIT_PER_MINUTE,
        "rate_limit_window_seconds": 60,
        "retries": OUTLOOK_RETRIES,
        "retry_delay_seconds": 0.0,
        "timeout_seconds": OUTLOOK_REQUEST_TIMEOUT_SECONDS,
    },
    "gmail": {
        "remetente": REMETENTE_GMAIL,
        "rate_limit": GMAIL_RATE_LIMIT_PER_MINUTE,
        "rate_limit_window_seconds": 60,
        "retries": GMAIL_RETRIES,
        "retry_delay_seconds": GMAIL_RETRY_DELAY_SECONDS,
        "timeout_seconds": 30.0,
    },
    "smtp": {
        "remetente": REMETENTE_SMTP,
        "rate_limit": SMTP_RATE_LIMIT,
        "rate_limit_window_seconds": SMTP_RATE_WINDOW_SECONDS,
        "retries": SMTP_RETRIES,
        "retry_delay_seconds": SMTP_RETRY_DELAY_SECONDS,
        "timeout_seconds": SMTP_TIMEOUT,
    },
}


def montar_configuracao(provedor: str | None = None) -> ComunicadoConfig:
    provider = (provedor or PROVEDOR_ENVIO).strip().lower()
    if provider not in PRESETS_POR_PROVEDOR:
        raise ValueError("PROVEDOR_ENVIO inválido. Use outlook, gmail ou smtp.")

    preset = PRESETS_POR_PROVEDOR[provider]
    return ComunicadoConfig(
        provider=provider,
        remetente=preset["remetente"],
        assunto=ASSUNTO,
        template=TEMPLATE_PDF,
        arquivo_emails=ARQUIVO_EMAILS,
        cartas_dir=CARTAS_DIR,
        arquivo_relatorio=ARQUIVO_RELATORIO,
        rate_limit=preset["rate_limit"],
        rate_limit_window_seconds=preset["rate_limit_window_seconds"],
        retries=preset["retries"],
        retry_delay_seconds=preset["retry_delay_seconds"],
        timeout_seconds=preset["timeout_seconds"],
    )


def main() -> None:
    executar_comunicado(montar_configuracao())


if __name__ == "__main__":
    main()
