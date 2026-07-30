import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services.bounce_gmail import (
    _extract_bounce_reason,
    _extract_recipient_from_body,
)
from services.bounce_outlook import _extract_recipient
from services.bounce_report import atualizar_relatorio_com_bounces


class BouncesTest(unittest.TestCase):
    def test_extrai_destinatario_e_motivo_gmail(self) -> None:
        body = (
            "Final-Recipient: rfc822; falha@example.com\n"
            "Action: failed\n"
            "Diagnostic-Code: smtp; 550 User unknown"
        )

        self.assertEqual(
            _extract_recipient_from_body(body),
            "falha@example.com",
        )
        self.assertEqual(_extract_bounce_reason(body), "Usuário desconhecido")

    def test_outlook_prioriza_destinatarios_do_relatorio(self) -> None:
        body = (
            "<p>Não foi possível entregar para suporte@example.com.</p>"
            "<p>Destinatário: falha@example.com</p>"
        )

        self.assertEqual(
            _extract_recipient(body, ["falha@example.com"]),
            "falha@example.com",
        )

    def test_atualiza_apenas_linha_enviada(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "report.xlsx"
            pd.DataFrame(
                [
                    {
                        "Destinatario": "falha@example.com",
                        "Status do envio": "Enviado",
                        "Erro": "N/A",
                    },
                    {
                        "Destinatario": "falha@example.com",
                        "Status do envio": "Falha",
                        "Erro": "erro anterior",
                    },
                ]
            ).to_excel(report, index=False)

            count = atualizar_relatorio_com_bounces(
                [
                    {
                        "Destinatario": "falha@example.com",
                        "Motivo do bounce": "550 User unknown",
                    }
                ],
                str(report),
            )
            result = pd.read_excel(report).fillna("")

        self.assertEqual(count, 1)
        self.assertEqual(result.iloc[0]["Status do envio"], "Falha")
        self.assertEqual(result.iloc[0]["Erro"], "550 User unknown")
        self.assertEqual(result.iloc[1]["Erro"], "erro anterior")


if __name__ == "__main__":
    unittest.main()
