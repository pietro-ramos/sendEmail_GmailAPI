from pathlib import Path

import pandas as pd


REPORT_COLUMNS = ["Destinatario", "Status do envio", "Erro"]


class Relatorio:
    def __init__(self, arquivo_relatorio: str) -> None:
        self.arquivo_relatorio = Path(arquivo_relatorio)

    def gerar_relatorio(self, resultados_envio) -> None:
        dataframe = pd.DataFrame(resultados_envio, columns=REPORT_COLUMNS)
        self.arquivo_relatorio.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(self.arquivo_relatorio, index=False)
        print(f"Relatório de envio salvo em '{self.arquivo_relatorio}'.")
