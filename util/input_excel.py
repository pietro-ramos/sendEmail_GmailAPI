import re
import unicodedata
from collections.abc import Iterable

import pandas as pd

from models.credor import Credor


def _normalize_header(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    normalized = normalized.encode("ASCII", "ignore").decode()
    return re.sub(r"\s+", " ", normalized.upper().strip())


def _clean_cell(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\u00a0", " ").strip()


def _sanitize_ascii(text: str, digits_only: bool = False) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    normalized = normalized.encode("ASCII", "ignore").decode()
    if digits_only:
        normalized = re.sub(r"[^0-9]", "", normalized)
    else:
        normalized = re.sub(r"[^A-Za-z0-9]", "_", normalized).upper()
    return re.sub(r"_+", "_", normalized).strip("_")[:50]


def _sanitize_punctuation(text: str) -> str:
    # Mantém compatibilidade com PDFs legados nomeados como QUIROGRAF_RIO.
    normalized = re.sub(r"[^\w]", "_", str(text or ""))
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ASCII", "ignore").decode()
    normalized = re.sub(r"[^A-Za-z0-9]", "_", normalized).upper()
    return re.sub(r"_+", "_", normalized).strip("_")[:50]


def gerar_nomes_candidatos_carta(
    nome: str,
    cpf_cnpj: str,
    classe: str,
) -> list[str]:
    del nome  # O contrato atual usa CPF/CNPJ e classe para localizar o PDF.
    documento = _sanitize_ascii(cpf_cnpj, digits_only=True)
    classes = [
        _sanitize_ascii(classe),
        _sanitize_punctuation(classe),
    ]

    variantes = []
    for value in classes:
        if not value or value in variantes:
            continue
        variantes.append(value)
        if value == "QUIROGRAFARIO" and "QUIROGRAF_RIO" not in variantes:
            variantes.append("QUIROGRAF_RIO")

    candidatos = [
        f"{documento}_{classe_normalizada}.pdf"
        for classe_normalizada in variantes
        if documento
    ]
    if documento:
        candidatos.append(f"{documento}.pdf")
    return candidatos


def _coluna_disponivel(
    dataframe: pd.DataFrame,
    aliases: Iterable[str],
    *,
    obrigatoria: bool = False,
) -> str | None:
    columns = {_normalize_header(column): column for column in dataframe.columns}
    aliases = tuple(aliases)
    for alias in aliases:
        match = columns.get(_normalize_header(alias))
        if match is not None:
            return match

    if obrigatoria:
        raise ValueError(
            "Coluna obrigatória não encontrada. "
            f"Esperado um de {list(aliases)}; encontrado {list(dataframe.columns)}."
        )
    return None


def carregar_credores(arquivo_emails: str) -> list[Credor]:
    dataframe = pd.read_excel(arquivo_emails, dtype=str).fillna("")

    columns = {
        "nome": _coluna_disponivel(
            dataframe,
            ["Nome do Credor", "Nome Credor", "Nome", "Razão Social/Nome"],
            obrigatoria=True,
        ),
        "email": _coluna_disponivel(
            dataframe,
            ["Email", "E-mail", "Email Principal"],
            obrigatoria=True,
        ),
        "cpf_cnpj": _coluna_disponivel(
            dataframe,
            ["CPF / CNPJ", "CPF/CNPJ", "CPF", "CNPJ/CPF", "CNPJ / CPF"],
            obrigatoria=True,
        ),
        "classe": _coluna_disponivel(
            dataframe,
            ["Classe", "Classe do Credor"],
        ),
        "valor": _coluna_disponivel(
            dataframe,
            ["Valor R$", "Valor (R$)", "Valor"],
        ),
        "endereco": _coluna_disponivel(
            dataframe,
            ["Endereço", "Endereco"],
        ),
        "natureza": _coluna_disponivel(
            dataframe,
            ["Natureza", "Natureza do Crédito", "Natureza/Origem"],
        ),
        "origem": _coluna_disponivel(
            dataframe,
            ["Origem", "Origem do Crédito", "Natureza/Origem"],
        ),
    }

    credores = []
    for _, row in dataframe.iterrows():
        values = {
            field: _clean_cell(row.get(column, "")) if column else ""
            for field, column in columns.items()
        }
        credores.append(Credor(**values))
    return credores
