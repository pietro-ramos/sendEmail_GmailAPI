import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from models.credor import Credor
from services.gmail_email import GmailEmailService
from services.graph_email import GraphEmailService
from services.preflight import (
    PreflightService,
    validar_endereco_email,
    validar_payload_graph,
)
from services.smtp_email import SmtpEmailService


class PreflightTest(unittest.TestCase):
    def _credor(self, email: str = "banco@example.com") -> Credor:
        return Credor(
            nome="Banco Exemplo",
            classe="QUIROGRAFARIO",
            valor="100",
            email=email,
            cpf_cnpj="123",
        )

    def test_valida_destinatario_sem_consultar_provedor(self) -> None:
        self.assertEqual(validar_endereco_email("banco@example.com"), [])
        self.assertTrue(validar_endereco_email("-"))
        self.assertTrue(validar_endereco_email("um@example.com;dois@example.com"))
        self.assertTrue(validar_endereco_email("sem-arroba.example.com"))

    def test_detecta_payload_graph_incompleto(self) -> None:
        payload = {
            "message": {
                "subject": "",
                "body": {"contentType": "HTML", "content": ""},
                "toRecipients": [],
                "attachments": [],
            }
        }

        erros, _ = validar_payload_graph(payload)

        self.assertTrue(any("assunto" in erro for erro in erros))
        self.assertTrue(any("destinatário" in erro for erro in erros))
        self.assertTrue(any("anexo PDF" in erro for erro in erros))
        self.assertTrue(any("saveToSentItems" in erro for erro in erros))

    def test_monta_payload_graph_com_sufixo_sem_enviar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_QUIROGRAFARIO_2.pdf").write_bytes(
                b"%PDF-1.7 test"
            )
            token_provider = Mock()
            service = GraphEmailService(
                token_provider=token_provider,
                remetente="sender@example.com",
                cartas_dir=temp_dir,
            )
            preflight = PreflightService(
                provider="outlook",
                email_service=service,
                remetente="sender@example.com",
            )

            with patch("services.graph_email.requests.post") as post:
                resultados = preflight.executar(
                    [self._credor()],
                    "Assunto",
                    "<p>{nome}</p>",
                )

        self.assertEqual(len(resultados), 1)
        self.assertTrue(resultados[0].aprovado, resultados[0].erros)
        self.assertEqual(
            resultados[0].anexos,
            ["123_QUIROGRAFARIO_2.pdf"],
        )
        self.assertGreater(resultados[0].tamanho_payload_bytes, 0)
        token_provider.get_token.assert_not_called()
        post.assert_not_called()

    def test_destinatario_invalido_reprova_sem_enviar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_QUIROGRAFARIO.pdf").write_bytes(
                b"%PDF-1.7 test"
            )
            service = GraphEmailService(
                token_provider=Mock(),
                remetente="sender@example.com",
                cartas_dir=temp_dir,
            )
            preflight = PreflightService(
                provider="outlook",
                email_service=service,
                remetente="sender@example.com",
            )

            with patch("services.graph_email.requests.post") as post:
                resultado = preflight.executar(
                    [self._credor(email="-")],
                    "Assunto",
                    "<p>{nome}</p>",
                )[0]

        self.assertFalse(resultado.aprovado)
        self.assertTrue(
            any("formato inválido" in erro for erro in resultado.erros)
        )
        self.assertGreater(resultado.tamanho_payload_bytes, 0)
        post.assert_not_called()

    def test_monta_payload_gmail_sem_enviar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_QUIROGRAFARIO.pdf").write_bytes(
                b"%PDF-1.7 test"
            )
            gmail_api = Mock()
            service = GmailEmailService(
                service=gmail_api,
                remetente="sender@example.com",
                cartas_dir=temp_dir,
            )
            resultado = PreflightService(
                provider="gmail",
                email_service=service,
                remetente="sender@example.com",
            ).executar(
                [self._credor()],
                "Assunto",
                "<p>{nome}</p>",
            )[0]

        self.assertTrue(resultado.aprovado, resultado.erros)
        self.assertGreater(resultado.tamanho_payload_bytes, 0)
        gmail_api.users.assert_not_called()

    def test_monta_payload_smtp_sem_abrir_conexao(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_QUIROGRAFARIO.pdf").write_bytes(
                b"%PDF-1.7 test"
            )
            service = SmtpEmailService(
                smtp_host="smtp.example.com",
                smtp_port=587,
                username="",
                password="",
                remetente="sender@example.com",
                require_auth=False,
                cartas_dir=temp_dir,
            )
            service._connect = Mock(
                side_effect=AssertionError("Conexão SMTP não permitida no preflight")
            )
            resultado = PreflightService(
                provider="smtp",
                email_service=service,
                remetente="sender@example.com",
            ).executar(
                [self._credor()],
                "Assunto",
                "<p>{nome}</p>",
            )[0]

        self.assertTrue(resultado.aprovado, resultado.erros)
        self.assertGreater(resultado.tamanho_payload_bytes, 0)
        service._connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
