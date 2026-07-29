class Credor:
    def __init__(self, nome, classe, valor, email, cpf_cnpj, endereco, natureza='', origem=''):
        self.nome = nome
        self.classe = classe
        self.valor = valor
        self.email = email
        self.cpf_cnpj = cpf_cnpj
        self.endereco = endereco
        self.natureza = natureza
        self.origem = origem

    def __repr__(self):
        return f"Credor({self.nome}, {self.email})"
