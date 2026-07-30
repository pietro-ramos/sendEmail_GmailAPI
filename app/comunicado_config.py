from dataclasses import dataclass
from typing import Literal


Provider = Literal["outlook", "gmail", "smtp"]


@dataclass(frozen=True)
class ComunicadoConfig:
    provider: Provider
    remetente: str
    assunto: str
    template: str
    arquivo_emails: str
    cartas_dir: str
    arquivo_relatorio: str
    rate_limit: int
    rate_limit_window_seconds: int
    retries: int
    retry_delay_seconds: float
    timeout_seconds: float

    def __post_init__(self) -> None:
        if self.provider not in {"outlook", "gmail", "smtp"}:
            raise ValueError("Provedor inválido. Use outlook, gmail ou smtp.")
        if not self.remetente.strip():
            raise ValueError(
                f"Remetente não configurado para o provedor {self.provider}."
            )
        if not self.assunto.strip():
            raise ValueError("O assunto do e-mail não pode ficar vazio.")
        if not self.arquivo_emails.strip():
            raise ValueError("O caminho da planilha não pode ficar vazio.")
        if not self.cartas_dir.strip():
            raise ValueError("O diretório de PDFs não pode ficar vazio.")
        if self.rate_limit < 1:
            raise ValueError("O limite de envio deve ser maior que zero.")
        if self.rate_limit_window_seconds < 1:
            raise ValueError("A janela do limite deve ser maior que zero.")
        if self.retries < 1:
            raise ValueError("A quantidade de tentativas deve ser maior que zero.")
        if self.retry_delay_seconds < 0:
            raise ValueError("O intervalo de retry não pode ser negativo.")
        if self.timeout_seconds <= 0:
            raise ValueError("O timeout deve ser maior que zero.")
