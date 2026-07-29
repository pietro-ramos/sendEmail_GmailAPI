from email.utils import parseaddr
from pathlib import Path

import pandas as pd

from config import TEMPLATE_ABM_TEMP_HTML
from models.credor import Credor


DIRETORIO_TEMP_ABM = Path("data/temp")
ARQUIVO_PLANILHA_ABM_TEMP = DIRETORIO_TEMP_ABM / "Dados_Merge_Cartas_ABM.xlsx"
ARQUIVO_PLANILHA_TESTE_ABM_TEMP = (
    DIRETORIO_TEMP_ABM / "teste_Dados_Merge_Cartas_ABM.xlsx"
)
ARQUIVO_REFERENCIA_CARTA_ABM_TEMP = (
    DIRETORIO_TEMP_ABM / "modelo_corpo_email.docx"
)
ARQUIVO_RELATORIO_OPENWEB_TEMP = DIRETORIO_TEMP_ABM / "relatorio_openweb_temp.xlsx"
ARQUIVO_HTML_PREVIEW_GMAIL_TEMP = DIRETORIO_TEMP_ABM / "preview_email_gmail.html"
ARQUIVO_HTML_PREVIEW_OPENWEB_TEMP = DIRETORIO_TEMP_ABM / "preview_email_openweb.html"
ARQUIVO_HTML_PREVIEW_OPENWEB_SIMULACAO_TEMP = (
    DIRETORIO_TEMP_ABM / "preview_email_openweb_simulacao.html"
)
ARQUIVO_RELATORIO_OPENWEB_SIMULACAO_TEMP = (
    DIRETORIO_TEMP_ABM / "relatorio_openweb_simulacao_temp.xlsx"
)
ARQUIVO_CREDENCIAIS_GMAIL_TEMP = Path("credentials_gmail_temp.json")
ARQUIVO_TOKEN_GMAIL_TEMP = Path("token_gmail_temp.json")

COLUNAS_OBRIGATORIAS = (
    "Credor",
    "Documento",
    "Endereco",
    "Creditos",
    "Orientacao",
    "Classe",
    "Email",
)


def _clean_cell(value: str) -> str:
    return str(value or "").replace("\u00a0", " ").strip()


def _email_valido(email: str) -> bool:
    _, endereco = parseaddr(email)
    return (
        bool(email)
        and endereco == email
        and endereco.count("@") == 1
        and not any(separador in email for separador in ",;")
    )


def carregar_credores_abm_temp(
    arquivo_planilha: Path = ARQUIVO_PLANILHA_ABM_TEMP,
) -> list[Credor]:
    if not arquivo_planilha.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {arquivo_planilha}")

    df = pd.read_excel(arquivo_planilha, dtype=str).fillna("")
    ausentes = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns]
    if ausentes:
        raise ValueError(
            "Planilha temporária ABM fora do modelo esperado. "
            f"Colunas ausentes: {ausentes}. Colunas encontradas: {list(df.columns)}"
        )

    lista_credores = []
    for _, row in df.iterrows():
        credor = Credor(
            nome=_clean_cell(row["Credor"]),
            classe=_clean_cell(row["Classe"]),
            valor=_clean_cell(row["Creditos"]),
            email=_clean_cell(row["Email"]),
            cpf_cnpj=_clean_cell(row["Documento"]),
            endereco=_clean_cell(row["Endereco"]),
            natureza="",
            origem=_clean_cell(row["Orientacao"]),
        )
        if any(
            (
                credor.nome,
                credor.email,
                credor.cpf_cnpj,
                credor.valor,
                credor.origem,
            )
        ):
            lista_credores.append(credor)

    if not lista_credores:
        raise ValueError(f"A planilha não contém credores: {arquivo_planilha}")
    return lista_credores


def construir_template_email_abm_temp() -> str:
    return TEMPLATE_ABM_TEMP_HTML


def selecionar_credor_teste(lista_credores: list[Credor]) -> Credor:
    return lista_credores[0]


def criar_credor_para_teste(credor_base: Credor, destinatario: str) -> Credor:
    return Credor(
        nome=credor_base.nome,
        classe=credor_base.classe,
        valor=credor_base.valor,
        email=destinatario,
        cpf_cnpj=credor_base.cpf_cnpj,
        endereco=credor_base.endereco,
        natureza=credor_base.natureza,
        origem=credor_base.origem,
    )


def validar_destinatario_unico(destinatario: str) -> str:
    destinatario = _clean_cell(destinatario)
    if not _email_valido(destinatario):
        raise ValueError(
            "TEMP_ABM_GMAIL_TEST_DESTINATARIO deve conter um único e-mail válido."
        )
    return destinatario


def validar_conta_gmail_temp(conta: str) -> str:
    conta = _clean_cell(conta).lower()
    if not _email_valido(conta):
        raise ValueError(
            "TEMP_ABM_GMAIL_CONTA deve conter o endereço completo da conta Gmail pessoal."
        )
    return conta


def separar_credores_por_email(
    lista_credores: list[Credor],
) -> tuple[list[Credor], list[dict]]:
    validos = []
    resultados_invalidos = []
    for linha, credor in enumerate(lista_credores, start=2):
        email = _clean_cell(credor.email)
        if _email_valido(email):
            validos.append(credor)
            continue
        resultados_invalidos.append(
            {
                "Destinatario": email,
                "Status do envio": "Falha",
                "Erro": f"E-mail ausente ou inválido na linha {linha}",
            }
        )
    return validos, resultados_invalidos
