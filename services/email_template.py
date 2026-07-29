from html import escape
from typing import Dict


def construir_contexto_template(credor) -> Dict[str, str]:
    campos = {
        "nome": str(credor.nome or ""),
        "classe": str(credor.classe or ""),
        "valor": str(credor.valor or ""),
        "cpf_cnpj": str(credor.cpf_cnpj or ""),
        "endereco": str(credor.endereco or ""),
        "natureza": str(credor.natureza or ""),
        "origem": str(credor.origem or ""),
    }

    contexto = {}
    for chave, valor in campos.items():
        texto = valor.replace("\r\n", "\n").replace("\r", "\n")
        texto_escapado = escape(texto)
        contexto[chave] = texto_escapado
        contexto[f"{chave}_html"] = texto_escapado.replace("\n", "<br>\n")
    return contexto


def renderizar_template_email(template: str, credor) -> str:
    return template.format(**construir_contexto_template(credor))
