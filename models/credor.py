from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Credor:
    nome: str
    classe: str
    valor: str
    email: str
    cpf_cnpj: str
    endereco: str = ""
    natureza: str = ""
    origem: str = ""
