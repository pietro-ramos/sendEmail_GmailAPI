import os
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# Função para buscar os emails sem destinatário e registrar os corpos em um documento
def registrar_corpos_emails(service, email_ids_file, output_file):
    # Verifica se o arquivo com IDs existe
    if not os.path.exists(email_ids_file):
        print(f"Arquivo {email_ids_file} não encontrado.")
        return

    # Lê os IDs dos emails sem destinatário do arquivo
    with open(email_ids_file, "r") as f:
        email_ids = [line.strip().split(": ")[1] for line in f.readlines()]

    # Abre o arquivo de saída para gravar os corpos dos emails
    with open(output_file, "w", encoding="utf-8") as output:
        for email_id in email_ids:
            try:
                # Busca o email no Gmail usando o ID
                msg = service.users().messages().get(userId='me', id=email_id).execute()
                payload = msg.get('payload', {})

                # Extrai o corpo do email
                body = get_body_from_payload(payload)

                # Registra o corpo do email no arquivo de saída
                output.write(f"E-mail ID: {email_id}\n")
                output.write(f"Corpo do E-mail:\n{body}\n")
                output.write("=" * 50 + "\n\n")  # Separador entre emails

                print(f"Corpo do e-mail ID {email_id} registrado.")

            except Exception as e:
                print(f"Erro ao processar o e-mail ID {email_id}: {e}")

    print(f"Corpos dos e-mails registrados em {output_file}.")


# Função para extrair o corpo do e-mail (reutilizando função existente)
def get_body_from_payload(payload):
    """
    Extrai o corpo do e-mail (bounce) do payload da mensagem.
    A mensagem pode ser dividida em várias partes, especialmente se for multipart (HTML, texto simples, etc.).
    Esta função tenta extrair o texto relevante, seja ele em formato HTML ou texto simples.
    """
    body = ""

    # Verifica se o payload tem múltiplas partes
    if 'parts' in payload:
        body = extract_body_from_parts(payload['parts'])
    else:
        # Se não houver múltiplas partes, trata o payload como uma única parte
        body = extract_body_from_parts([payload])

    return body


# Função auxiliar para extrair corpo do email, parte por parte
def extract_body_from_parts(parts):
    body = ""

    for part in parts:
        # Verifica o tipo MIME da parte (HTML ou texto)
        mime_type = part.get('mimeType', '')

        # Se o tipo MIME for 'text/plain' ou 'text/html', decodifica o conteúdo
        if mime_type in ['text/plain', 'text/html']:
            body_data = part.get('body', {}).get('data', '')
            if body_data:
                # Decodifica o corpo da mensagem (Base64 para texto)
                body += base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')

        # Se houver partes internas (como em mensagens multipart), as processa recursivamente
        elif 'parts' in part:
            body += extract_body_from_parts(part.get('parts', []))

    return body


# Função para autenticar e criar o serviço Gmail (reutilizar função existente)
def get_gmail_service():
    creds = None
    token_file = 'token.json'
    credentials_file = 'credentials.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, ['https://www.googleapis.com/auth/gmail.readonly'])
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


# Função principal para rodar o script
def main():
    service = get_gmail_service()

    # Define os arquivos de input (IDs) e output (corpos)
    email_ids_file = "emails_sem_destinatario.txt"
    output_file = "corpos_emails_para_analise.txt"

    # Executa a função para registrar os corpos dos emails
    registrar_corpos_emails(service, email_ids_file, output_file)


if __name__ == '__main__':
    main()
