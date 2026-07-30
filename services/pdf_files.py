from pathlib import Path

from util.input_excel import gerar_nomes_candidatos_carta


def localizar_pdfs(cartas_dir: str, credor) -> list[Path]:
    directory = Path(cartas_dir)
    if not directory.is_dir():
        return []

    candidatos = gerar_nomes_candidatos_carta(
        credor.nome,
        credor.cpf_cnpj,
        credor.classe,
    )
    for filename in candidatos:
        primary = directory / filename
        if not primary.is_file():
            continue

        encontrados = [primary]
        index = 2
        while True:
            extra = primary.with_name(f"{primary.stem}_{index}{primary.suffix}")
            if not extra.is_file():
                break
            encontrados.append(extra)
            index += 1
        return encontrados

    return []


def nome_anexo(credor, index: int) -> str:
    if index == 0:
        return f"Comunicado - {credor.nome}.pdf"
    return f"Comunicado - {credor.nome} ({index + 1}).pdf"
