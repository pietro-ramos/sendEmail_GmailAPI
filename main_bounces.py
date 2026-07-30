from config import BOUNCE_PROVIDER, BOUNCE_REPORT_FILE
from services.bounce_gmail import buscar_bounces_gmail
from services.bounce_outlook import buscar_bounces_outlook
from services.bounce_report import (
    atualizar_relatorio_com_bounces,
    obter_destinatarios_relatorio,
)


def main() -> None:
    destinatarios = obter_destinatarios_relatorio(BOUNCE_REPORT_FILE)

    if BOUNCE_PROVIDER == "outlook":
        bounces = buscar_bounces_outlook(destinatarios_alvo=destinatarios)
    elif BOUNCE_PROVIDER == "gmail":
        bounces = buscar_bounces_gmail()
    else:
        raise ValueError("BOUNCE_PROVIDER inválido. Use outlook ou gmail.")

    atualizar_relatorio_com_bounces(bounces, BOUNCE_REPORT_FILE)


if __name__ == "__main__":
    main()
