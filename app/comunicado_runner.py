from app.comunicado_config import ComunicadoConfig
from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    LOCAWEB_API_TOKEN,
    LOCAWEB_API_URL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_REQUIRE_AUTH,
    SMTP_SECURITY,
    SMTP_TIMEOUT,
    SMTP_USERNAME,
    TENANT_ID,
)
from services.auth import Auth
from services.graph_auth import GraphAuth
from services.graph_email import GraphEmailService
from services.graph_email_exterior import GraphEmailServiceExterior
from services.locaweb_email import LocawebEmailService
from services.relatorio import Relatorio
from services.send_email import EmailService
from services.smtp_email import SmtpEmailService
from util.input_excel import carregar_credores, carregar_credores_exterior


def _carregar_lista(configuracao: ComunicadoConfig):
    if configuracao.lista_exterior:
        return carregar_credores_exterior(
            configuracao.arquivo_emails,
            configuracao.classe_exterior,
        )
    return carregar_credores(configuracao.arquivo_emails)


def _executar_outlook(configuracao: ComunicadoConfig, lista_credores):
    auth = GraphAuth(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    print("Token do Graph obtido com sucesso")

    classe_servico = (
        GraphEmailServiceExterior
        if configuracao.usar_busca_pdf_exterior
        else GraphEmailService
    )
    email_service = classe_servico(
        token_provider=auth,
        remetente=configuracao.remetente,
        rate_limit_per_min=configuracao.rate_limit_per_min,
        retries=configuracao.retries,
        cartas_dir=configuracao.cartas_dir,
        require_pdf=configuracao.require_pdf,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
        configuracao.imagem_path,
    )


def _executar_gmail(configuracao: ComunicadoConfig, lista_credores):
    auth = Auth()
    service = auth.get_service()
    print("Autenticacao concluida com sucesso")

    email_service = EmailService(
        service,
        configuracao.remetente,
        cartas_dir=configuracao.cartas_dir,
        require_pdf=configuracao.require_pdf,
        rate_limit_per_min=configuracao.rate_limit_per_min,
        retries=configuracao.retries,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
        configuracao.imagem_path,
    )


def _executar_locaweb(configuracao: ComunicadoConfig, lista_credores):
    email_service = LocawebEmailService(
        api_token=LOCAWEB_API_TOKEN,
        api_url=LOCAWEB_API_URL,
        remetente=configuracao.remetente,
        rate_limit_per_min=configuracao.rate_limit_per_min,
        retries=configuracao.retries,
        cartas_dir=configuracao.cartas_dir,
        require_pdf=configuracao.require_pdf,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
    )


def _executar_smtp(configuracao: ComunicadoConfig, lista_credores):
    email_service = SmtpEmailService(
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        remetente=configuracao.remetente,
        security_mode=SMTP_SECURITY,
        timeout=SMTP_TIMEOUT,
        require_auth=SMTP_REQUIRE_AUTH,
        rate_limit_per_min=configuracao.rate_limit_per_min,
        retries=configuracao.retries,
        cartas_dir=configuracao.cartas_dir,
        require_pdf=configuracao.require_pdf,
    )
    return email_service.enviar_emails_em_massa(
        lista_credores,
        configuracao.assunto,
        configuracao.template,
        configuracao.imagem_path,
    )


def executar_comunicado(configuracao: ComunicadoConfig):
    lista_credores = _carregar_lista(configuracao)
    print(
        f"Carregados {len(lista_credores)} credores do arquivo "
        f"{configuracao.arquivo_emails}"
    )
    print(
        f"Iniciando envio via {configuracao.provider} para "
        f"{len(lista_credores)} credores..."
    )

    if configuracao.provider == "outlook":
        logs_envio = _executar_outlook(configuracao, lista_credores)
    elif configuracao.provider == "gmail":
        logs_envio = _executar_gmail(configuracao, lista_credores)
    elif configuracao.provider == "locaweb":
        logs_envio = _executar_locaweb(configuracao, lista_credores)
    elif configuracao.provider == "smtp":
        logs_envio = _executar_smtp(configuracao, lista_credores)
    else:
        raise ValueError(
            "Provedor invalido. Use 'outlook', 'gmail', 'locaweb' ou 'smtp'."
        )

    print("Envio de e-mails concluido")
    Relatorio().gerar_relatorio(logs_envio)
