import argparse
import getpass
import sys
from pathlib import Path

from app.temp_abm_email import (
    ARQUIVO_CREDENCIAIS_GMAIL_TEMP,
    ARQUIVO_HTML_PREVIEW_GMAIL_TEMP,
    ARQUIVO_PLANILHA_TESTE_ABM_TEMP,
    ARQUIVO_TOKEN_GMAIL_TEMP,
    carregar_credores_abm_temp,
    construir_template_email_abm_temp,
    separar_credores_por_email,
    selecionar_credor_teste,
    validar_conta_gmail_temp,
)
from config import (
    TEMP_ABM_ASSUNTO,
    TEMP_ABM_GMAIL_APP_PASSWORD,
    TEMP_ABM_GMAIL_CONTA,
    TEMP_ABM_GMAIL_SMTP_HOST,
    TEMP_ABM_GMAIL_SMTP_PASSWORD,
    TEMP_ABM_GMAIL_SMTP_PORT,
    TEMP_ABM_GMAIL_SMTP_REQUIRE_AUTH,
    TEMP_ABM_GMAIL_SMTP_SECURITY,
    TEMP_ABM_GMAIL_SMTP_USERNAME,
)
from services.email_template import renderizar_template_email
from services.smtp_email import SmtpEmailService


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera o preview ABM e, opcionalmente, envia todos os registros do teste via Gmail."
    )
    parser.add_argument(
        "--enviar",
        action="store_true",
        help="Autentica no Gmail e envia todos os registros válidos da planilha de teste. Sem esta flag, apenas gera o HTML.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    lista_credores = carregar_credores_abm_temp(
        ARQUIVO_PLANILHA_TESTE_ABM_TEMP
    )
    credor_base = selecionar_credor_teste(lista_credores)

    credores_validos, _ = separar_credores_por_email(lista_credores)
    if not credores_validos:
        raise ValueError(
            f"A planilha de teste não contém destinatários válidos: {ARQUIVO_PLANILHA_TESTE_ABM_TEMP}"
        )

    template_email = construir_template_email_abm_temp()

    html_renderizado = renderizar_template_email(template_email, credor_base)
    Path(ARQUIVO_HTML_PREVIEW_GMAIL_TEMP).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    Path(ARQUIVO_HTML_PREVIEW_GMAIL_TEMP).write_text(
        html_renderizado,
        encoding="utf-8",
    )
    print(
        f"Preview gerado com o primeiro registro de "
        f"'{ARQUIVO_PLANILHA_TESTE_ABM_TEMP}'."
    )
    print(f"HTML salvo em '{ARQUIVO_HTML_PREVIEW_GMAIL_TEMP}'.")

    if not args.enviar:
        print(
            f"Nenhum e-mail enviado. Use --enviar para disparar os {len(credores_validos)} destinatários válidos da planilha de teste."
        )
        return

    print(
        f"Enviando {len(credores_validos)} e-mails de teste a partir da planilha "
        f"{ARQUIVO_PLANILHA_TESTE_ABM_TEMP}"
    )

    if ARQUIVO_CREDENCIAIS_GMAIL_TEMP.is_file():
        conta_gmail = validar_conta_gmail_temp(TEMP_ABM_GMAIL_CONTA)

        from services.auth import Auth
        from services.send_email import EmailService

        auth = Auth(
            token_path=ARQUIVO_TOKEN_GMAIL_TEMP,
            credentials_path=ARQUIVO_CREDENCIAIS_GMAIL_TEMP,
            force_browser_login=True,
        )
        service = auth.get_service()
        perfil = service.users().getProfile(userId="me").execute()
        remetente = (perfil.get("emailAddress") or "").strip().lower()
        if remetente != conta_gmail:
            raise ValueError(
                f"Conta Gmail autenticada incorreta: {remetente or '<não identificada>'}. "
                f"Selecione {conta_gmail}. Nenhum e-mail foi enviado."
            )
        print(f"Autenticação Gmail concluída para {remetente}.")

        email_service = EmailService(
            service,
            remetente,
            cartas_dir=None,
            require_pdf=False,
            rate_limit_per_min=1,
            retries=1,
        )

        resultados = email_service.enviar_emails_em_massa(
            credores_validos,
            TEMP_ABM_ASSUNTO,
            template_email,
            imagem_path="",
        )
    else:
        resultados = _enviar_por_smtp(credores_validos, template_email)

    falhas = [resultado for resultado in resultados if resultado["Status do envio"] != "Enviado"]
    for resultado in resultados:
        print(resultado)
    if falhas:
        raise RuntimeError(
            f"Falha no envio Gmail para {len(falhas)} destinatário(s)."
        )


def _enviar_por_smtp(
    lista_credores,
    template_email: str,
) -> list[dict[str, str]]:
    smtp_username = TEMP_ABM_GMAIL_SMTP_USERNAME or TEMP_ABM_GMAIL_CONTA
    smtp_password = TEMP_ABM_GMAIL_SMTP_PASSWORD or TEMP_ABM_GMAIL_APP_PASSWORD

    if not smtp_username and sys.stdin.isatty():
        smtp_username = input(
            "Digite o endereço Gmail para o teste SMTP: "
        ).strip().lower()
    if not smtp_password and sys.stdin.isatty():
        smtp_password = getpass.getpass(
            "Digite a senha de aplicativo do Gmail: "
        )

    if not smtp_username or not smtp_password:
        raise FileNotFoundError(
            "Credencial OAuth temporária não encontrada e SMTP do Gmail não configurado. "
            "Defina TEMP_ABM_GMAIL_SMTP_USERNAME e TEMP_ABM_GMAIL_SMTP_PASSWORD "
            "ou informe as credenciais no terminal quando solicitado."
        )

    print(
        "credentials_gmail_temp.json não encontrado; usando SMTP do Gmail "
        "como alternativa gratuita para o teste."
    )
    smtp_service = SmtpEmailService(
        smtp_host=TEMP_ABM_GMAIL_SMTP_HOST,
        smtp_port=TEMP_ABM_GMAIL_SMTP_PORT,
        username=smtp_username,
        password=smtp_password,
        remetente=smtp_username,
        security_mode=TEMP_ABM_GMAIL_SMTP_SECURITY,
        require_auth=TEMP_ABM_GMAIL_SMTP_REQUIRE_AUTH,
        rate_limit_per_min=1,
        retries=1,
        cartas_dir=None,
        require_pdf=False,
    )
    return smtp_service.enviar_emails_em_massa(
        lista_credores,
        TEMP_ABM_ASSUNTO,
        template_email,
        imagem_path="",
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Erro: {exc}") from exc
