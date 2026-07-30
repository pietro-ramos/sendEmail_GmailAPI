import re
from pathlib import Path

import pandas as pd


def normalize_email(value: str) -> str:
    return re.sub(
        r"\s+",
        "",
        str(value or "").replace("\u00a0", ""),
    ).strip().lower()


def _localizar_coluna_destinatario(dataframe: pd.DataFrame) -> str | None:
    for candidate in ("Destinatario", "Destinatário"):
        if candidate in dataframe.columns:
            return candidate
    return None


def _status_enviado(value: str) -> bool:
    return str(value or "").strip().lower() == "enviado"


def obter_destinatarios_relatorio(arquivo_relatorio: str) -> list[str]:
    report_path = Path(arquivo_relatorio)
    if not report_path.is_file():
        raise FileNotFoundError(f"Relatório de envio não encontrado: {report_path}")

    dataframe = pd.read_excel(report_path)
    destination_column = _localizar_coluna_destinatario(dataframe)
    if not destination_column:
        raise ValueError("Coluna de destinatário não encontrada no relatório.")

    if "Status do envio" in dataframe.columns:
        dataframe = dataframe[
            dataframe["Status do envio"].apply(_status_enviado)
        ]

    destinatarios = []
    vistos = set()
    for value in dataframe[destination_column].dropna().astype(str):
        email = normalize_email(value)
        if not email or email in vistos:
            continue
        vistos.add(email)
        destinatarios.append(email)
    return destinatarios


def atualizar_relatorio_com_bounces(
    bounces: list[dict[str, str]],
    arquivo_relatorio: str,
) -> int:
    if not bounces:
        print("Nenhum bounce encontrado.")
        return 0

    dataframe = pd.read_excel(arquivo_relatorio)
    destination_column = _localizar_coluna_destinatario(dataframe)
    if not destination_column:
        raise ValueError("Coluna de destinatário não encontrada no relatório.")

    status_column_existed = "Status do envio" in dataframe.columns
    if "Motivo do bounce" not in dataframe.columns:
        dataframe["Motivo do bounce"] = ""
    if "Status do envio" not in dataframe.columns:
        dataframe["Status do envio"] = ""
    for column in ("Status do envio", "Motivo do bounce", "Erro"):
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].astype("object")

    dataframe["__dest_norm"] = dataframe[destination_column].apply(
        normalize_email
    )
    linhas_atualizadas = 0

    for bounce in bounces:
        destination = normalize_email(bounce.get("Destinatario", ""))
        reason = bounce.get("Motivo do bounce", "")
        mask = dataframe["__dest_norm"] == destination
        if status_column_existed:
            mask &= dataframe["Status do envio"].apply(_status_enviado)

        if not mask.any():
            continue
        dataframe.loc[mask, "Status do envio"] = "Falha"
        dataframe.loc[mask, "Motivo do bounce"] = reason
        if "Erro" in dataframe.columns:
            dataframe.loc[mask, "Erro"] = reason
        linhas_atualizadas += int(mask.sum())

    dataframe = dataframe.drop(columns=["__dest_norm"])
    dataframe.to_excel(arquivo_relatorio, index=False)
    print(
        f"Bounces encontrados: {len(bounces)} | "
        f"linhas atualizadas: {linhas_atualizadas}."
    )
    return linhas_atualizadas
