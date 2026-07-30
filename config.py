import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro.") from exc
    if value < minimum:
        raise ValueError(f"{name} deve ser maior ou igual a {minimum}.")
    return value


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número.") from exc
    if value < minimum:
        raise ValueError(f"{name} deve ser maior ou igual a {minimum}.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} deve ser true ou false.")


if load_dotenv:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    _load_env_fallback(ENV_PATH)


# Fluxo comum
PROVEDOR_ENVIO = os.getenv("PROVEDOR_ENVIO", "outlook").strip().lower()
ARQUIVO_EMAILS = os.getenv(
    "EMAIL_INPUT_FILE",
    "data/direct_lista_cartas.xlsx",
).strip()
CARTAS_DIR = os.getenv("EMAIL_PDF_DIR", "data/cartas").strip()
ARQUIVO_RELATORIO = os.getenv(
    "EMAIL_REPORT_FILE",
    "relatorio_bounces.xlsx",
).strip()
ARQUIVO_LOG = os.getenv("EMAIL_LOG_FILE", "email_log.log").strip()
ASSUNTO = os.getenv(
    "EMAIL_SUBJECT",
    "AVISO AOS CREDORES - RECUPERAÇÃO JUDICIAL",
).strip()


# Outlook / Microsoft Graph
REMETENTE = os.getenv("EMAIL_REMETENTE_OUTLOOK", "").strip()
TENANT_ID = os.getenv("GRAPH_TENANT_ID", "").strip()
CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
OUTLOOK_RATE_LIMIT_PER_MINUTE = _env_int(
    "OUTLOOK_RATE_LIMIT_PER_MINUTE",
    30,
)
OUTLOOK_RETRIES = _env_int("OUTLOOK_RETRIES", 3)
OUTLOOK_REQUEST_TIMEOUT_SECONDS = _env_float(
    "OUTLOOK_REQUEST_TIMEOUT_SECONDS",
    30.0,
    minimum=0.1,
)


# Gmail API
REMETENTE_GMAIL = os.getenv("EMAIL_REMETENTE_GMAIL", "").strip()
GMAIL_CREDENTIALS_FILE = os.getenv(
    "GMAIL_CREDENTIALS_FILE",
    "credentials.json",
).strip()
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json").strip()
GMAIL_RATE_LIMIT_PER_MINUTE = _env_int(
    "GMAIL_RATE_LIMIT_PER_MINUTE",
    120,
)
GMAIL_RETRIES = _env_int("GMAIL_RETRIES", 3)
GMAIL_RETRY_DELAY_SECONDS = _env_float(
    "GMAIL_RETRY_DELAY_SECONDS",
    5.0,
)


# SMTP genérico
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SECURITY = os.getenv("SMTP_SECURITY", "starttls").strip().lower()
SMTP_TIMEOUT = _env_float("SMTP_TIMEOUT", 60.0, minimum=0.1)
SMTP_REQUIRE_AUTH = _env_bool("SMTP_REQUIRE_AUTH", True)
SMTP_RATE_LIMIT = _env_int("SMTP_RATE_LIMIT", 40)
SMTP_RATE_WINDOW_SECONDS = _env_int("SMTP_RATE_WINDOW_SECONDS", 3600)
SMTP_RETRIES = _env_int("SMTP_RETRIES", 3)
SMTP_RETRY_DELAY_SECONDS = _env_float(
    "SMTP_RETRY_DELAY_SECONDS",
    5.0,
)
REMETENTE_SMTP = os.getenv(
    "EMAIL_REMETENTE_SMTP",
    SMTP_USERNAME,
).strip()


# Captura de bounces
BOUNCE_PROVIDER = os.getenv("BOUNCE_PROVIDER", "outlook").strip().lower()
BOUNCE_REPORT_FILE = os.getenv(
    "BOUNCE_REPORT_FILE",
    ARQUIVO_RELATORIO,
).strip()
BOUNCE_AFTER_DATE_GMAIL = os.getenv(
    "BOUNCE_AFTER_DATE_GMAIL",
    "2026-01-01",
).strip()
BOUNCE_AFTER_DATE_OUTLOOK = os.getenv(
    "BOUNCE_AFTER_DATE_OUTLOOK",
    "2026-01-01",
).strip()
BOUNCE_MAX_MESSAGES = _env_int("BOUNCE_MAX_MESSAGES", 3000)
BOUNCE_PAGE_SIZE = _env_int("BOUNCE_PAGE_SIZE", 300)
BOUNCE_REQUEST_TIMEOUT_SECONDS = _env_float(
    "BOUNCE_REQUEST_TIMEOUT_SECONDS",
    60.0,
    minimum=0.1,
)
GMAIL_BOUNCE_CREDENTIALS_FILE = os.getenv(
    "GMAIL_BOUNCE_CREDENTIALS_FILE",
    GMAIL_CREDENTIALS_FILE,
).strip()
GMAIL_BOUNCE_TOKEN_FILE = os.getenv(
    "GMAIL_BOUNCE_TOKEN_FILE",
    "token_bounces.json",
).strip()


# Único corpo de e-mail ativo: comunicado com PDF obrigatório.
TEMPLATE_PDF = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviso aos Credores</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1c1c1c; }}
        p {{ margin: 0 0 12px 0; }}
    </style>
</head>
<body>
    <p>Prezado(a) credor(a),</p>
    <p>Em anexo segue informativo a respeito da respectiva falência.</p>
    <p>Pedimos por gentileza que leia o arquivo com atenção.</p>
    <p>Havendo dúvidas, estamos à disposição pelo WhatsApp 51 99305-0115
    (somente mensagens) e pelo e-mail
    <a href="mailto:admjud@scalzilliaj.com.br">admjud@scalzilliaj.com.br</a>.</p>
    <p>Atenciosamente,<br>
    SCALZILLI, VINHAS &amp; VICENTE ADMINISTRAÇÃO JUDICIAL LTDA.</p>
</body>
</html>
"""
