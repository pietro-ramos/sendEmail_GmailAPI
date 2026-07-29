from dataclasses import dataclass
from typing import Literal


Provider = Literal["outlook", "gmail", "locaweb", "smtp"]


@dataclass(frozen=True)
class ComunicadoConfig:
    provider: Provider
    remetente: str
    assunto: str
    template: str
    arquivo_emails: str
    imagem_path: str = ""
    cartas_dir: str = ""
    require_pdf: bool = True
    lista_exterior: bool = False
    usar_busca_pdf_exterior: bool = False
    classe_exterior: str = ""
    rate_limit_per_min: int = 30
    retries: int = 3
