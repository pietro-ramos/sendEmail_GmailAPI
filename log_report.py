import re
from pathlib import Path

import pandas as pd

from util.input_excel import _sanitize_ascii, gerar_nomes_candidatos_carta

LOG_PATH = Path("email_log.log")
SAIDA = Path("email_log.xlsx")

INFO_PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Email para (?P<dest>[^ ]+) - Status: (?P<status>[^-]+?)(?: - Erro: (?P<erro>.*))?$"
)
ERROR_PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ERROR - (?P<msg>.*)$"
)


def parse_log(log_path: Path):
    envios = []
    erros = []
    if not log_path.exists():
        raise FileNotFoundError(f"Log não encontrado: {log_path}")

    current_dest = None
    current_classe = None
    current_cnpj = None

    with log_path.open(encoding="utf-8", errors="ignore") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if "Nenhum PDF encontrado para" in line and "candidatos:" in line:
                match_list = re.search(r"candidatos: \[(.+)\]", line)
                if match_list:
                    raw = match_list.group(1)
                    first = raw.split(",")[0].strip().strip("'\" ")
                    if "_" in first:
                        parts = first.replace(".pdf", "").split("_", 1)
                        cnpj = parts[0]
                        classe = parts[1] if len(parts) > 1 else ""
                        current_cnpj = cnpj
                        current_classe = classe
            match_info = INFO_PATTERN.match(line)
            if match_info:
                current_dest = match_info.group("dest").strip()
                envios.append(
                    {
                        "DataHora": match_info.group("ts"),
                        "Destinatario": current_dest,
                        "Status": match_info.group("status").strip(),
                        "Erro": (match_info.group("erro") or "").strip(),
                    }
                )
                continue
            match_err = ERROR_PATTERN.match(line)
            if match_err:
                email_in_err = None
                mail = re.search(r"([\w\.\-+%]+@[\w\.-]+\.[A-Za-z]{2,})", match_err.group("msg"))
                if mail:
                    email_in_err = mail.group(1)
                dest_for_err = email_in_err or current_dest or "(desconhecido)"

                anexos = []
                if current_cnpj:
                    classe_norm = _sanitize_ascii(current_classe or "")
                    for filename in gerar_nomes_candidatos_carta("", current_cnpj, classe_norm):
                        anexos.append(filename)
                erros.append(
                    {
                        "DataHora": match_err.group("ts"),
                        "Destinatario": dest_for_err,
                        "Mensagem": match_err.group("msg"),
                        "AnexoSugerido": anexos[0] if anexos else "",
                    }
                )
                continue
    return envios, erros


def gerar_excel(envios, erros, saida: Path):
    if not envios and not erros:
        print("Nada a exportar: sem registros de envio ou erro.")
        return
    with pd.ExcelWriter(saida, engine="xlsxwriter") as writer:
        if envios:
            pd.DataFrame(envios).to_excel(writer, sheet_name="envios", index=False)
        if erros:
            pd.DataFrame(erros).to_excel(writer, sheet_name="erros", index=False)
    print(f"Relatório salvo em {saida}")


def main():
    envios, erros = parse_log(LOG_PATH)
    gerar_excel(envios, erros, SAIDA)


if __name__ == "__main__":
    main()
