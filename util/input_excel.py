import pandas as pd
from models.credor import Credor

def carregar_credores(arquivo_emails):
    df = pd.read_excel(arquivo_emails)
    lista_credores = []

    for _, row in df.iterrows():
        credor = Credor(
            nome=row['Nome do Credor'],
            classe=row['Classe'],
            valor=row['Valor R$'],
            email=row['Email'],
            cpf_cnpj=row['CPF / CNPJ'],
            endereco=row['Endereço']
        )
        lista_credores.append(credor)

    return lista_credores
