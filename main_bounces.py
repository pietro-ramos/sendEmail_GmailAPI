from pathlib import Path

from config import ARQUIVO_RELATORIO, BOUNCE_PROVIDER_DEFAULT
# from services.bounce_gmail import buscar_bounces_gmail
from services.bounce_outlook import buscar_bounces_outlook
from services.bounce_report import (
    atualizar_relatorio_com_bounces,
    obter_destinatarios_relatorio,
)

# Provedor para captura de bounces: "outlook" ou "gmail"
PROVEDOR_BOUNCES = BOUNCE_PROVIDER_DEFAULT  
ARQUIVO_RELATORIO_BOUNCES = Path(__file__).resolve().parent / ARQUIVO_RELATORIO


def main():
    destinatarios_alvo = obter_destinatarios_relatorio(str(ARQUIVO_RELATORIO_BOUNCES))

    if PROVEDOR_BOUNCES == "outlook":
        bounces = buscar_bounces_outlook(destinatarios_alvo=destinatarios_alvo)
    elif PROVEDOR_BOUNCES == "gmail":
        # bounces = buscar_bounces_gmail()
        pass
    else:
        raise ValueError("PROVEDOR_BOUNCES invalido. Use 'outlook' ou 'gmail'.")

    atualizar_relatorio_com_bounces(bounces, str(ARQUIVO_RELATORIO_BOUNCES))


if __name__ == "__main__":
    main()
