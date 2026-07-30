import argparse

from app.preflight_runner import executar_preflight
from main import montar_configuracao
from services.preflight import ResultadoPreflight


def _mascarar_email(value: str) -> str:
    local, separator, domain = str(value or "").partition("@")
    if not separator:
        return value or "(vazio)"
    prefix = local[:2] if len(local) > 2 else local[:1]
    return f"{prefix}***@{domain}"


def _exibir_resultado(
    resultado: ResultadoPreflight,
    mostrar_aprovados: bool,
) -> None:
    if resultado.aprovado and not resultado.avisos and not mostrar_aprovados:
        return

    status = "OK" if resultado.aprovado else "FALHA"
    destinatario = _mascarar_email(resultado.destinatario)
    print(
        f"[{status}] linha {resultado.linha_planilha} | "
        f"{resultado.nome or '(sem nome)'} | {destinatario}"
    )
    for erro in resultado.erros:
        print(f"  ERRO: {erro}")
    for aviso in resultado.avisos:
        print(f"  AVISO: {aviso}")
    if resultado.aprovado and mostrar_aprovados:
        anexos = ", ".join(resultado.anexos)
        print(
            f"  Payload: {resultado.tamanho_payload_bytes} bytes | "
            f"Anexos: {anexos}"
        )


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Monta e valida todos os payloads do lote sem autenticar "
            "e sem enviar e-mails."
        )
    )
    parser.add_argument(
        "--provider",
        choices=("outlook", "gmail", "smtp"),
        help="Sobrescreve PROVEDOR_ENVIO somente neste preflight.",
    )
    parser.add_argument(
        "--mostrar-aprovados",
        action="store_true",
        help="Exibe também cada payload aprovado.",
    )
    return parser.parse_args()


def main() -> int:
    args = _argumentos()
    configuracao = montar_configuracao(args.provider)
    print(
        f"Preflight sem envio: {configuracao.provider} | "
        f"planilha={configuracao.arquivo_emails} | "
        f"PDFs={configuracao.cartas_dir}"
    )
    resultados = executar_preflight(configuracao)
    for resultado in resultados:
        _exibir_resultado(resultado, args.mostrar_aprovados)

    total = len(resultados)
    falhas = sum(not resultado.aprovado for resultado in resultados)
    avisos = sum(bool(resultado.avisos) for resultado in resultados)
    aprovados = total - falhas
    print(
        f"Resumo: {total} linhas | {aprovados} aprovadas | "
        f"{falhas} com erro | {avisos} com aviso."
    )
    print(
        "Nenhum e-mail foi enviado. A validação de endereço é sintática; "
        "não confirma a existência da caixa postal."
    )
    return 1 if falhas else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        print(f"[FALHA] Não foi possível executar o preflight: {exc}")
        raise SystemExit(2) from None
