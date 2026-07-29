import os

from app import ComunicadoConfig, executar_comunicado
from config import (
    ARQUIVO_EMAILS,
    ASSUNTO,
    ASSUNTO_SMTP,
    CARTAS_DIR,
    CLASSE_EXTERIOR,
    RATE_LIMIT_PER_MIN,
    REMETENTE,
    REMETENTE_SMTP,
    RETRIES,
    SMTP_RATE_LIMIT_PER_HOUR,
    TEMPLATE_PDF,
)

# === BLOCO UNICO DE CONFIGURACAO DO COMUNICADO ===
# Fluxo padrao mantido em Outlook/Microsoft Graph com PDF anexo.
PROVEDOR_ENVIO = (os.getenv("PROVEDOR_ENVIO") or "outlook").strip().lower()

# Ajustes principais do comunicado
ARQUIVO_PLANILHA = ARQUIVO_EMAILS
ENVIAR_COM_PDF = True
USAR_LISTA_EXTERIOR = False
USAR_BUSCA_PDF_EXTERIOR = False

# Opcional: sobrescreva os valores padrao do provedor ativo
ASSUNTO_CUSTOM = ""
TEMPLATE_CUSTOM = ""
REMETENTE_CUSTOM = ""
IMAGEM_CUSTOM = ""
# ===============================================

PRESETS_POR_PROVEDOR = {
    "outlook": {
        "remetente": REMETENTE,
        "assunto": ASSUNTO,
        "template": TEMPLATE_PDF,
        "imagem_path": "",
    },
    "smtp": {
        "remetente": REMETENTE_SMTP,
        "assunto": ASSUNTO_SMTP,
        "template": TEMPLATE_PDF,
        "imagem_path": "",
    },
}


def _montar_configuracao() -> ComunicadoConfig:
    if PROVEDOR_ENVIO not in PRESETS_POR_PROVEDOR:
        raise ValueError(
            "PROVEDOR_ENVIO inválido neste ponto de entrada. "
            "Use 'outlook' (padrão) ou 'smtp'."
        )
    if not ENVIAR_COM_PDF:
        raise ValueError("Fluxo ativo exige PDF anexo. Mantenha ENVIAR_COM_PDF=True.")
    if USAR_LISTA_EXTERIOR or USAR_BUSCA_PDF_EXTERIOR:
        raise ValueError(
            "Fluxo exterior esta desativado neste ponto de entrada durante a reestruturacao."
        )

    preset = PRESETS_POR_PROVEDOR[PROVEDOR_ENVIO]

    assunto = ASSUNTO_CUSTOM.strip() or preset["assunto"]
    template = TEMPLATE_CUSTOM or preset["template"]
    remetente = REMETENTE_CUSTOM.strip() or preset["remetente"]
    imagem_path = IMAGEM_CUSTOM.strip() or preset["imagem_path"]

    return ComunicadoConfig(
        provider=PROVEDOR_ENVIO,
        remetente=remetente,
        assunto=assunto,
        template=template,
        arquivo_emails=ARQUIVO_PLANILHA,
        imagem_path=imagem_path,
        cartas_dir=CARTAS_DIR,
        require_pdf=ENVIAR_COM_PDF,
        lista_exterior=USAR_LISTA_EXTERIOR,
        usar_busca_pdf_exterior=USAR_BUSCA_PDF_EXTERIOR,
        classe_exterior=CLASSE_EXTERIOR,
        rate_limit_per_min=(
            SMTP_RATE_LIMIT_PER_HOUR if PROVEDOR_ENVIO == "smtp" else RATE_LIMIT_PER_MIN
        ),
        retries=RETRIES,
    )


def main():
    configuracao = _montar_configuracao()
    executar_comunicado(configuracao)


if __name__ == "__main__":
    main()
