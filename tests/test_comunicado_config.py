import unittest

from app.comunicado_config import ComunicadoConfig


def build_config(**overrides) -> ComunicadoConfig:
    values = {
        "provider": "outlook",
        "remetente": "sender@example.com",
        "assunto": "Assunto",
        "template": "<p>Comunicado</p>",
        "arquivo_emails": "data/credores.xlsx",
        "cartas_dir": "data/cartas",
        "arquivo_relatorio": "email_log.xlsx",
        "rate_limit": 30,
        "rate_limit_window_seconds": 60,
        "retries": 3,
        "retry_delay_seconds": 5.0,
        "timeout_seconds": 30.0,
    }
    values.update(overrides)
    return ComunicadoConfig(**values)


class ComunicadoConfigTest(unittest.TestCase):
    def test_aceita_somente_tres_provedores_ativos(self) -> None:
        for provider in ("outlook", "gmail", "smtp"):
            self.assertEqual(build_config(provider=provider).provider, provider)

        with self.assertRaisesRegex(ValueError, "Provedor inválido"):
            build_config(provider="locaweb")

    def test_rejeita_limites_invalidos(self) -> None:
        with self.assertRaisesRegex(ValueError, "limite"):
            build_config(rate_limit=0)
        with self.assertRaisesRegex(ValueError, "tentativas"):
            build_config(retries=0)


if __name__ == "__main__":
    unittest.main()
