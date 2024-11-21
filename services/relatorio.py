import pandas as pd
from config import ARQUIVO_RELATORIO

class Relatorio:
    def gerar_relatorio(self, resultados_envio):
        df = pd.DataFrame(resultados_envio)
        self.salvar_relatorio(df)

    def salvar_relatorio(self, df):
        df.to_excel(ARQUIVO_RELATORIO, index=False)
        print(f"Relatório de bounces salvo em '{ARQUIVO_RELATORIO}'.")
