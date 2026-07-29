import re
import unicodedata

import pandas as pd
from models.credor import Credor

        
def _normalize_header(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode()
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_cell(value: str) -> str:
    return str(value or "").replace("\u00a0", " ").strip()


def _sanitize_ascii(text: str, digits_only: bool = False) -> str:
    text = text or ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    if digits_only:
        text = re.sub(r"[^0-9]", "", text)
    else:
        text = re.sub(r"[^A-Za-z0-9]", "_", text)
        text = text.upper()
    text = re.sub(r"_+", "_", text).strip('_')
    return text[:50]


def _sanitize_punct_to_underscore(text: str) -> str:
    """Versão que troca qualquer não-alfanumérico por '_' antes de remover acento.
    Compatível com nomes já existentes do tipo QUIROGRAF_RIO.
    """
    text = text or ""
    text = re.sub(r"[^\w]", "_", text)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    text = re.sub(r"[^A-Za-z0-9]", "_", text)
    text = text.upper()
    text = re.sub(r"_+", "_", text).strip('_')
    return text[:50]


def normalizar_nome_arquivo(nome: str) -> str:
    """Normaliza o nome do credor para o formato usado nos arquivos PDF.
    Mesmo algoritmo do sistema gerador de documentos (padrão antigo RDV)."""
    safe_filename = ''.join(c if c.isalnum() else '_' for c in nome)
    safe_filename = safe_filename[:50]
    return safe_filename + '.pdf'


def gerar_nomes_candidatos_carta(nome: str, cpf_cnpj: str, classe: str) -> list[str]:
    """Gera nomes candidatos no padrão <CNPJ>_<CLASSE>.pdf ou <CNPJ>.pdf.

    - CNPJ/CPF: só dígitos
    - Classe: alfanumérico, acentos removidos, não alfanum vira '_'
    """
    cnpj_clean = _sanitize_ascii(cpf_cnpj, digits_only=True)
    classe_clean_a = _sanitize_ascii(classe, digits_only=False)
    classe_clean_b = _sanitize_punct_to_underscore(classe)

    classe_variants = []
    for c in [classe_clean_a, classe_clean_b]:
        if not c:
            continue
        classe_variants.append(c)
        # Alias específico para o padrão antigo "QUIROGRAF_RIO"
        if c.upper() == "QUIROGRAFARIO":
            classe_variants.append("QUIROGRAF_RIO")

    candidatos = []
    for classe_clean in classe_variants:
        if cnpj_clean and classe_clean:
            candidatos.append(f"{cnpj_clean}_{classe_clean}.pdf")
    if cnpj_clean:
        candidatos.append(f"{cnpj_clean}.pdf")
    return candidatos


def gerar_nomes_candidatos_carta_exterior(nome: str, classe: str) -> list[str]:
    """Gera nomes candidatos usando somente o nome (sem CNPJ).

    - Nome: sanitizado para ASCII, substituindo não alfanum por '_'
    - Classe: usa variação com underscores para manter compatibilidade
    """
    nome_clean = _sanitize_punct_to_underscore(nome)
    classe_clean = _sanitize_punct_to_underscore(classe)

    candidatos = []
    if nome_clean and classe_clean:
        candidatos.append(f"{nome_clean}_{classe_clean}.pdf")
    if nome_clean:
        candidatos.append(f"{nome_clean}.pdf")
    return candidatos


def _coluna_disponivel(df, aliases, obrigatoria=False):
    cols_map = {_normalize_header(c): c for c in df.columns}
    for alias in aliases:
        found = cols_map.get(_normalize_header(alias))
        if found:
            return found
    if obrigatoria:
        raise ValueError(
            f"Colunas necessárias não encontradas. Esperado qualquer um de {aliases}, encontrado {list(df.columns)}"
        )
    return None


def carregar_credores(arquivo_emails):
    df = pd.read_excel(arquivo_emails, dtype=str).fillna("")

    nome_col = _coluna_disponivel(df, ['Nome do Credor', 'Nome Credor', 'Nome', 'Razao Social/Nome'], obrigatoria=True)
    email_col = _coluna_disponivel(df, ['Email', 'E-mail', 'E-MAIL', 'Email Principal'], obrigatoria=True)
    cpf_col = _coluna_disponivel(df, ['CPF / CNPJ', 'CPF/CNPJ', 'CPF', 'CNPJ/CPF', 'CNPJ / CPF'], obrigatoria=True)
    classe_col = _coluna_disponivel(df, ['Classe', 'Classe do Credor'])
    valor_col = _coluna_disponivel(df, ['Valor R$', 'Valor (R$)', 'Valor', 'VALOR'])
    endereco_col = _coluna_disponivel(df, ['Endereço', 'Endereco'])
    natureza_col = _coluna_disponivel(df, ['Natureza', 'Natureza do Crédito', 'Natureza/Origem', 'NATUREZA'])
    origem_col = _coluna_disponivel(df, ['Origem', 'Origem do Crédito', 'Natureza/Origem', 'ORIGEM'])

    lista_credores = []
    for _, row in df.iterrows():
        credor = Credor(
            nome=_clean_cell(row.get(nome_col, '')),
            classe=_clean_cell(row.get(classe_col, '')) if classe_col else '',
            valor=_clean_cell(row.get(valor_col, '')) if valor_col else '',
            email=_clean_cell(row.get(email_col, '')),
            cpf_cnpj=_clean_cell(row.get(cpf_col, '')),
            endereco=_clean_cell(row.get(endereco_col, '')) if endereco_col else '',
            natureza=_clean_cell(row.get(natureza_col, '')) if natureza_col else '',
            origem=_clean_cell(row.get(origem_col, '')) if origem_col else ''
        )
        lista_credores.append(credor)

    return lista_credores


def carregar_credores_exterior(arquivo_emails, classe_padrao: str):
    df = pd.read_excel(arquivo_emails, dtype=str).fillna("")

    nome_col = _coluna_disponivel(df, ['Nome do Credor', 'Nome Credor', 'Nome'], obrigatoria=True)
    email_col = _coluna_disponivel(df, ['Email', 'E-mail'], obrigatoria=True)
    classe_col = _coluna_disponivel(df, ['Classe', 'Classe do Credor'])
    moeda_col = _coluna_disponivel(df, ['Moeda', 'Currency'])
    valor_col = _coluna_disponivel(df, ['Valor R$', 'Valor (R$)', 'Valor'])
    endereco_col = _coluna_disponivel(df, ['Endereço', 'Endereco'])
    natureza_col = _coluna_disponivel(df, ['Natureza', 'Natureza do Crédito', 'Natureza/Origem'])
    origem_col = _coluna_disponivel(df, ['Origem', 'Origem do Crédito', 'Natureza/Origem'])

    lista_credores = []
    for _, row in df.iterrows():
        moeda = row.get(moeda_col, '') if moeda_col else ''
        valor_raw = row.get(valor_col, '') if valor_col else ''
        valor_fmt = f"{moeda} {valor_raw}".strip() if moeda or valor_raw else ''

        credor = Credor(
            nome=row.get(nome_col, ''),
            classe=row.get(classe_col, '') if classe_col else classe_padrao,
            valor=valor_fmt,
            email=row.get(email_col, ''),
            cpf_cnpj='',  # Sem CNPJ para credores do exterior
            endereco=row.get(endereco_col, '') if endereco_col else '',
            natureza=row.get(natureza_col, '') if natureza_col else '',
            origem=row.get(origem_col, '') if origem_col else ''
        )
        lista_credores.append(credor)

    return lista_credores