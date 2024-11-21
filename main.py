from config import REMETENTE, ASSUNTO, TEMPLATE, ARQUIVO_EMAILS, IMAGEM_PATH
from services.auth import Auth
from services.send_email import EmailService
from util.input_excel import carregar_credores


def main():
    # Carrega a lista de credores
    lista_credores = carregar_credores(ARQUIVO_EMAILS)

    # Autenticação e obtenção do serviço Gmail
    auth = Auth()
    service = auth.get_service()

    # Inicializa o serviço de envio de e-mails
    email_service = EmailService(service, REMETENTE)

    # Envia e-mails com controle de taxa e retry
    email_service.enviar_emails_em_massa(lista_credores, ASSUNTO, TEMPLATE, IMAGEM_PATH)


if __name__ == '__main__':
    main()
