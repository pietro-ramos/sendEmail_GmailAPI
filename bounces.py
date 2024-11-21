import os
import base64
import re
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime
from config import ARQUIVO_RELATORIO

# Define a data de corte para filtrar os emails recebidos
DATA_CORTE = datetime(2024, 11, 1)

# Função para autenticar e criar o serviço Gmail
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

    return build('gmail', 'v1', credentials=creds)


# Função para buscar e-mails com o assunto "Delivery Status Notification" ou "Undeliverable"

def search_bounces(service):
    # Adiciona a data de corte diretamente na consulta para o filtro
    query = 'subject:"Delivery Status Notification" OR subject:"Undeliverable: Informações Importantes para Credores" OR subject:"Problema ao entregar o e-mail - retorno ao remetente" after:2024/11/01'
    response = service.users().messages().list(userId='me', q=query).execute()
    messages = response.get('messages', [])
    next_page_token = response.get('nextPageToken', None)

    bounce_records = []
    total_messages_processed = 0
    emails_without_recipient = []

    while messages:
        for message in messages:
            total_messages_processed += 1
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])

            # Código restante para extração de destinatário e motivo do bounce...
            failed_recipient = None
            for header in headers:
                if header['name'] == 'X-Failed-Recipients':
                    failed_recipient = header['value']
                    break

            body = get_body_from_payload(payload)
            if not failed_recipient:
                failed_recipient = extract_recipient_from_body(body)

            bounce_reason = extract_bounce_reason(body)

            if failed_recipient == "Destinatário desconhecido":
                emails_without_recipient.append(message['id'])

            if failed_recipient:
                bounce_records.append({
                    'Destinatário': failed_recipient,
                    'Motivo do bounce': bounce_reason
                })

        if next_page_token:
            response = service.users().messages().list(userId='me', q=query, pageToken=next_page_token).execute()
            messages = response.get('messages', [])
            next_page_token = response.get('nextPageToken', None)
        else:
            break

    print(f"Total de e-mails processados: {total_messages_processed}")
    print(f"Total de e-mails sem destinatário identificado: {len(emails_without_recipient)}")

    if emails_without_recipient:
        with open("emails_sem_destinatario.txt", "w") as f:
            for email_id in emails_without_recipient:
                f.write(f"E-mail ID: {email_id}\n")
        print("Relatório de e-mails sem destinatário salvo em 'emails_sem_destinatario.txt'.")

    return bounce_records



def extract_recipient_from_body(body):
    patterns = [
        r'Endereço de e-mail ([^ ]+) não pôde ser encontrado',
        r'Usuário desconhecido: ([^\n]+)',
        r'mensagem para <a.*?><b>([^<]+)</b></a>',
        r'Final-Recipient: rfc822; ([^\n]+)',
        r'(\S+@\S+\.\S+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Destinatário desconhecido"


def extract_bounce_reason(body):
    patterns = [
        r'Caixa de entrada do destinatário está cheia',
        r'Caixa de entrada do destinatário está cheia ou está recebendo muitos e-mails',
        r'The recipient\'s inbox is out of storage space',
        r'O Gmail tentará novamente por mais \d+ horas',
        r'452 4.2.2.*The recipient\'s inbox is out of storage space',
        r'Ocorreu um problema temporário na entrega da mensagem para [^\n]+',
        r'Sua mensagem não foi entregue a [^ ]+ porque ([^\n]+)',
        r'Action: failed\nDiagnostic-Code: smtp; ([^\n]+)',
        r'Endereço não encontrado',
        r'The recipient server did not accept our requests to connect. ([^\n]+)',
        r'The recipient\'s mailbox is full',
        r'User unknown'
    ]

    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()

    return "Motivo desconhecido"


def get_body_from_payload(payload):
    body = ""
    if 'parts' in payload:
        body = extract_body_from_parts(payload['parts'])
    else:
        body = extract_body_from_parts([payload])
    return body


def extract_body_from_parts(parts):
    body = ""
    for part in parts:
        mime_type = part.get('mimeType', '')
        if mime_type in ['text/plain', 'text/html']:
            body_data = part.get('body', {}).get('data', '')
            if body_data:
                body += base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        elif 'parts' in part:
            body += extract_body_from_parts(part.get('parts', []))
    return body


def atualizar_relatorio_com_bounces(bounces):
    df = pd.read_excel(ARQUIVO_RELATORIO)
    for bounce in bounces:
        destinatario = bounce['Destinatário']
        motivo_bounce = bounce['Motivo do bounce']
        mask = df['Destinatário'] == destinatario
        if mask.any():
            df.loc[mask, 'Status do envio'] = 'Falha'
            df.loc[mask, 'Motivo do bounce'] = motivo_bounce
    df.to_excel(ARQUIVO_RELATORIO, index=False)
    print(f"Relatório atualizado com bounces salvo em '{ARQUIVO_RELATORIO}'.")


def main():
    service = get_gmail_service()
    print('Buscando bounces...')
    bounce_records = search_bounces(service)
    if bounce_records:
        print("Atualizando o relatório com os bounces encontrados...")
        atualizar_relatorio_com_bounces(bounce_records)
    else:
        print("Nenhum bounce encontrado para atualizar o relatório.")


if __name__ == '__main__':
    main()
