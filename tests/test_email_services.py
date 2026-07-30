import base64
import smtplib
import tempfile
import unittest
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import Mock, patch

from models.credor import Credor
from services.gmail_email import GmailEmailService
from services.graph_email import GraphEmailService
from services.smtp_email import SmtpEmailService


class FakeTokenProvider:
    def get_token(self) -> str:
        return "token-for-test"


class FakeSmtpClient:
    def __init__(self, error=None) -> None:
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def send_message(self, *args, **kwargs) -> None:
        if self.error:
            raise self.error


class EmailServicesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.credor = Credor(
            nome="<Banco Exemplo>",
            classe="II",
            valor="100",
            email=" banco@example.com ",
            cpf_cnpj="123",
        )

    def test_gmail_monta_mensagem_com_pdf_e_html_escapado(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_II.pdf").write_bytes(b"%PDF-test")
            service = GmailEmailService(
                service=object(),
                remetente="sender@example.com",
                cartas_dir=temp_dir,
            )

            raw = service._criar_mensagem(
                self.credor,
                "Assunto",
                "<p>{nome}</p>",
            )
            message = BytesParser(policy=policy.default).parsebytes(
                base64.urlsafe_b64decode(raw)
            )

        self.assertEqual(message["To"], "banco@example.com")
        self.assertEqual(len(list(message.iter_attachments())), 1)
        html_part = message.get_body(preferencelist=("html",))
        self.assertIn("&lt;Banco Exemplo&gt;", html_part.get_content())

    def test_graph_monta_payload_com_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "123_II.pdf").write_bytes(b"%PDF-test")
            service = GraphEmailService(
                FakeTokenProvider(),
                "sender@example.com",
                cartas_dir=temp_dir,
            )

            payload = service._build_payload(
                self.credor,
                "Assunto",
                "<p>{nome}</p>",
            )

        self.assertIsNotNone(payload)
        message = payload["message"]
        self.assertEqual(
            message["toRecipients"][0]["emailAddress"]["address"],
            "banco@example.com",
        )
        self.assertIn("&lt;Banco Exemplo&gt;", message["body"]["content"])
        self.assertEqual(len(message["attachments"]), 1)

    def test_smtp_retry_usa_intervalo_configurado(self) -> None:
        service = SmtpEmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="",
            password="",
            remetente="sender@example.com",
            require_auth=False,
            retries=2,
            retry_delay_seconds=0.25,
        )
        service._connect = Mock(
            side_effect=[
                FakeSmtpClient(smtplib.SMTPDataError(451, b"temporary")),
                FakeSmtpClient(),
            ]
        )

        with patch("services.smtp_email.time.sleep") as sleep:
            status, error = service._send_with_retries(
                "recipient@example.com",
                EmailMessage(),
            )

        self.assertEqual((status, error), ("Enviado", "N/A"))
        sleep.assert_called_once_with(0.25)
        self.assertEqual(service._connect.call_count, 2)

    def test_smtp_auto_nao_faz_downgrade_para_texto_claro(self) -> None:
        service = SmtpEmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="",
            password="",
            remetente="sender@example.com",
            require_auth=False,
            security_mode="auto",
        )
        service._connect_with_mode = Mock(side_effect=OSError("TLS indisponível"))

        with self.assertRaises(OSError):
            service._connect()

        service._connect_with_mode.assert_called_once_with("starttls")


if __name__ == "__main__":
    unittest.main()
