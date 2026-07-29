import argparse

import pandas as pd

from app.temp_abm_email import (
    ARQUIVO_HTML_PREVIEW_OPENWEB_TEMP,
    ARQUIVO_HTML_PREVIEW_OPENWEB_SIMULACAO_TEMP,
    ARQUIVO_PLANILHA_ABM_TEMP,
    ARQUIVO_PLANILHA_TESTE_ABM_TEMP,
    ARQUIVO_RELATORIO_OPENWEB_TEMP,
    ARQUIVO_RELATORIO_OPENWEB_SIMULACAO_TEMP,
    carregar_credores_abm_temp,
    construir_template_email_abm_temp,
    separar_credores_por_email,
)
from config import (
    OPENWEB_TEMP_SMTP_HOST,
    OPENWEB_TEMP_SMTP_PASSWORD,
    OPENWEB_TEMP_SMTP_PORT,
    OPENWEB_TEMP_SMTP_REQUIRE_AUTH,
    OPENWEB_TEMP_SMTP_SECURITY,
    OPENWEB_TEMP_SMTP_TIMEOUT,
    OPENWEB_TEMP_SMTP_USERNAME,
    OPENWEB_TEMP_RATE_LIMIT_PER_HOUR,
    RETRIES,
    TEMP_ABM_ASSUNTO,
)
from services.email_template import renderizar_template_email
from services.smtp_email import SmtpEmailService


def salvar_relatorio_openweb_temp(resultados_envio: list[dict]) -> None:
    ARQUIVO_RELATORIO_OPENWEB_TEMP.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(resultados_envio)
    df.to_excel(ARQUIVO_RELATORIO_OPENWEB_TEMP, index=False)
    print(f"Relatório salvo em '{ARQUIVO_RELATORIO_OPENWEB_TEMP}'.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida o lote ABM e, opcionalmente, envia via Openweb."
    )
    parser.add_argument(
        "--simular",
        action="store_true",
        help="Usa a planilha de teste em data/temp para simular o envio Openweb antes do oficial.",
    )
    parser.add_argument(
        "--enviar",
        action="store_true",
        help="Envia o lote selecionado. Sem esta flag, apenas valida e gera o preview.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    arquivo_planilha = (
        ARQUIVO_PLANILHA_TESTE_ABM_TEMP if args.simular else ARQUIVO_PLANILHA_ABM_TEMP
    )
    arquivo_preview = (
        ARQUIVO_HTML_PREVIEW_OPENWEB_SIMULACAO_TEMP
        if args.simular
        else ARQUIVO_HTML_PREVIEW_OPENWEB_TEMP
    )
    arquivo_relatorio = (
        ARQUIVO_RELATORIO_OPENWEB_SIMULACAO_TEMP
        if args.simular
        else ARQUIVO_RELATORIO_OPENWEB_TEMP
    )

    lista_credores = carregar_credores_abm_temp(arquivo_planilha)
    credores_validos, resultados_invalidos = separar_credores_por_email(
        lista_credores
    )
    if not credores_validos:
        raise ValueError("A planilha não contém nenhum destinatário válido.")
    template_email = construir_template_email_abm_temp()

    html_preview = renderizar_template_email(template_email, credores_validos[0])
    arquivo_preview.write_text(
        html_preview,
        encoding="utf-8",
    )

    modo = "SIMULAÇÃO" if args.simular else "OFICIAL"
    print(
        f"Modo {modo}: carregados {len(lista_credores)} registros de '{arquivo_planilha}'. "
        f"{len(credores_validos)} destinatários válidos e {len(resultados_invalidos)} inválidos."
    )
    print(f"Preview salvo em '{arquivo_preview}'.")
    if not args.enviar:
        print(
            f"Nenhum e-mail enviado. Use --enviar para confirmar o lote {modo.lower()} Openweb."
        )
        return

    if not OPENWEB_TEMP_SMTP_USERNAME or not OPENWEB_TEMP_SMTP_PASSWORD:
        raise ValueError(
            "Defina OPENWEB_TEMP_SMTP_USERNAME e OPENWEB_TEMP_SMTP_PASSWORD no .env."
        )

    print(f"Iniciando envio via Openweb no modo {modo.lower()} com corpo HTML temporário ABM...")
    email_service = SmtpEmailService(
        smtp_host=OPENWEB_TEMP_SMTP_HOST,
        smtp_port=OPENWEB_TEMP_SMTP_PORT,
        username=OPENWEB_TEMP_SMTP_USERNAME,
        password=OPENWEB_TEMP_SMTP_PASSWORD,
        remetente=OPENWEB_TEMP_SMTP_USERNAME,
        security_mode=OPENWEB_TEMP_SMTP_SECURITY,
        timeout=OPENWEB_TEMP_SMTP_TIMEOUT,
        require_auth=OPENWEB_TEMP_SMTP_REQUIRE_AUTH,
        rate_limit_per_min=OPENWEB_TEMP_RATE_LIMIT_PER_HOUR,
        rate_limit_window_seconds=3600,
        retries=RETRIES,
        cartas_dir=None,
        require_pdf=False,
    )

    resultados_validos = email_service.enviar_emails_em_massa(
        credores_validos,
        TEMP_ABM_ASSUNTO,
        template_email,
        imagem_path="",
    )
    resultados_envio = resultados_invalidos + resultados_validos

    print("Envio de e-mails concluído.")
    if args.simular:
        arquivo_relatorio.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(resultados_envio).to_excel(arquivo_relatorio, index=False)
        print(f"Relatório da simulação salvo em '{arquivo_relatorio}'.")
    else:
        salvar_relatorio_openweb_temp(resultados_envio)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Erro: {exc}") from exc
