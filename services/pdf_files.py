import re
from pathlib import Path

from util.input_excel import gerar_nomes_candidatos_carta


def _localizar_variantes_numeradas(
    directory: Path,
    primary: Path,
) -> list[tuple[int, Path]]:
    pattern = re.compile(
        rf"^{re.escape(primary.stem)}_(\d+){re.escape(primary.suffix)}$",
        flags=re.IGNORECASE,
    )
    encontrados = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = pattern.fullmatch(path.name)
        if not match:
            continue
        index = int(match.group(1))
        if index >= 2:
            encontrados.append((index, path))
    return sorted(encontrados, key=lambda item: item[0])


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
        encontrados = [primary] if primary.is_file() else []
        encontrados.extend(
            path
            for _, path in _localizar_variantes_numeradas(directory, primary)
        )
        if encontrados:
            return encontrados

    return []


def nome_anexo(credor, index: int) -> str:
    if index == 0:
        return f"Comunicado - {credor.nome}.pdf"
    return f"Comunicado - {credor.nome} ({index + 1}).pdf"
