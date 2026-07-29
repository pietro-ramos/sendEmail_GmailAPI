import re
from typing import Dict, List

import pandas as pd


def normalize_email(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").replace("\u00a0", "")).strip().lower()


def _localizar_coluna_destinatario(df: pd.DataFrame) -> str | None:
    for candidate in ("Destinatario", "Destinatário"):
        if candidate in df.columns:
            return candidate
    return None


def _status_enviado(value: str) -> bool:
    return str(value or "").strip().lower() == "enviado"


def obter_destinatarios_relatorio(arquivo_relatorio: str) -> List[str]:
    df = pd.read_excel(arquivo_relatorio)
    dest_col = _localizar_coluna_destinatario(df)
    if not dest_col:
        return []

    if "Status do envio" in df.columns:
        df = df[df["Status do envio"].apply(_status_enviado)]

    destinatarios: List[str] = []
    vistos: set[str] = set()
    for value in df[dest_col].dropna().astype(str):
        email = normalize_email(value)
        if not email or email == "desconhecido" or email in vistos:
            continue
        vistos.add(email)
        destinatarios.append(email)
    return destinatarios


def atualizar_relatorio_com_bounces(
    bounces: List[Dict[str, str]],
    arquivo_relatorio: str,
) -> None:
    if not bounces:
        print("Nenhum bounce encontrado.")
        return

    df = pd.read_excel(arquivo_relatorio)
    dest_col = _localizar_coluna_destinatario(df)
    if not dest_col:
        print("Coluna de destinatário não encontrada no relatório; nenhuma linha atualizada.")
        return

    status_col_existia = "Status do envio" in df.columns
    if "Motivo do bounce" not in df.columns:
        df["Motivo do bounce"] = ""
    if "Status do envio" not in df.columns:
        df["Status do envio"] = ""
    for col in ("Status do envio", "Motivo do bounce", "Erro"):
        if col in df.columns:
            df[col] = df[col].astype("object")

    df["__dest_norm"] = df[dest_col].astype(str).apply(normalize_email)
    linhas_atualizadas = 0
    correspondencias = 0

    for bounce in bounces:
        destinatario = bounce.get("Destinatario", "")
        motivo_bounce = bounce.get("Motivo do bounce", "")
        mask_destinatario = df["__dest_norm"] == normalize_email(destinatario)
        correspondencias += int(mask_destinatario.sum())

        if status_col_existia:
            mask_status = df["Status do envio"].apply(_status_enviado)
            mask = mask_destinatario & mask_status
        else:
            mask = mask_destinatario

        if mask.any():
            df.loc[mask, "Status do envio"] = "Falha"
            df.loc[mask, "Motivo do bounce"] = motivo_bounce
            if "Erro" in df.columns:
                df.loc[mask, "Erro"] = motivo_bounce
            linhas_atualizadas += int(mask.sum())

    df = df.drop(columns=["__dest_norm"])
    df.to_excel(arquivo_relatorio, index=False)
    print(
        f"Bounces processados: {len(bounces)} | "
        f"Correspondências no relatório: {correspondencias} | "
        f"Linhas atualizadas: {linhas_atualizadas}"
    )
    print(f"Relatório atualizado com bounces salvo em '{arquivo_relatorio}'.")
