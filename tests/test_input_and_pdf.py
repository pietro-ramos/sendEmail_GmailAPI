import tempfile
import unittest
from pathlib import Path

import pandas as pd

from models.credor import Credor
from services.pdf_files import localizar_pdfs
from util.input_excel import (
    carregar_credores,
    gerar_nomes_candidatos_carta,
)


class InputAndPdfTest(unittest.TestCase):
    def test_preserva_alias_de_nome_pdf_legado(self) -> None:
        names = gerar_nomes_candidatos_carta(
            "Credor",
            "00.000.000/0001-91",
            "Quirografário",
        )

        self.assertEqual(
            names,
            [
                "00000000000191_QUIROGRAFARIO.pdf",
                "00000000000191_QUIROGRAF_RIO.pdf",
                "00000000000191.pdf",
            ],
        )

    def test_carrega_aliases_da_planilha(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            spreadsheet = Path(temp_dir) / "credores.xlsx"
            pd.DataFrame(
                [
                    {
                        "Razão Social/Nome": "Banco Exemplo",
                        "E-mail": " banco@example.com ",
                        "CNPJ / CPF": "00.000.000/0001-91",
                        "Classe do Credor": "II",
                    }
                ]
            ).to_excel(spreadsheet, index=False)

            credores = carregar_credores(str(spreadsheet))

        self.assertEqual(len(credores), 1)
        self.assertEqual(credores[0].nome, "Banco Exemplo")
        self.assertEqual(credores[0].email, "banco@example.com")
        self.assertEqual(credores[0].classe, "II")

    def test_localiza_pdf_principal_e_sufixos(self) -> None:
        credor = Credor(
            nome="Banco",
            classe="II",
            valor="",
            email="banco@example.com",
            cpf_cnpj="123",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "123_II.pdf").write_bytes(b"%PDF-1")
            (directory / "123_II_2.pdf").write_bytes(b"%PDF-2")

            paths = localizar_pdfs(str(directory), credor)

        self.assertEqual(
            [path.name for path in paths],
            ["123_II.pdf", "123_II_2.pdf"],
        )

    def test_localiza_sufixo_sem_exigir_arquivo_principal(self) -> None:
        credor = Credor(
            nome="Banco",
            classe="QUIROGRAFARIO",
            valor="",
            email="banco@example.com",
            cpf_cnpj="123",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "123_QUIROGRAFARIO_2.pdf").write_bytes(b"%PDF-2")

            paths = localizar_pdfs(str(directory), credor)

        self.assertEqual(
            [path.name for path in paths],
            ["123_QUIROGRAFARIO_2.pdf"],
        )


if __name__ == "__main__":
    unittest.main()
