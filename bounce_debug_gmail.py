import os

from services.bounce_gmail import _get_body_from_payload, get_gmail_service_readonly


def registrar_corpos_emails(service, email_ids_file: str, output_file: str) -> None:
    if not os.path.exists(email_ids_file):
        print(f"Arquivo {email_ids_file} não encontrado.")
        return

    with open(email_ids_file, "r", encoding="utf-8") as file:
        email_ids = [line.strip().split(": ")[1] for line in file.readlines()]

    with open(output_file, "w", encoding="utf-8") as output:
        for email_id in email_ids:
            try:
                msg = service.users().messages().get(userId="me", id=email_id).execute()
                payload = msg.get("payload", {})
                body = _get_body_from_payload(payload)

                output.write(f"E-mail ID: {email_id}\n")
                output.write(f"Corpo do E-mail:\n{body}\n")
                output.write("=" * 50 + "\n\n")
                print(f"Corpo do e-mail ID {email_id} registrado.")
            except Exception as exc:
                print(f"Erro ao processar o e-mail ID {email_id}: {exc}")

    print(f"Corpos dos e-mails registrados em {output_file}.")


def main():
    service = get_gmail_service_readonly()
    registrar_corpos_emails(
        service=service,
        email_ids_file="emails_sem_destinatario.txt",
        output_file="corpos_emails_para_analise.txt",
    )


if __name__ == "__main__":
    main()
