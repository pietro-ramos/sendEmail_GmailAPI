import base64
import time
import logging
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError


class EmailService:
    def __init__(self, service, remetente):
        self.service = service
        self.remetente = remetente
        self.enviados_no_minuto = 0
        self.limite_minuto = 150  # Ajuste conforme limite de API
        self.tentativas = 3  # Número de tentativas para emails com falha

        # Configuração de logging para auditoria
        logging.basicConfig(filename='email_log.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def enviar_emails_em_massa(self, lista_credores, assunto, template, imagem_path):
        logs_envio = []

        for i, credor in enumerate(lista_credores):
            if self.enviados_no_minuto >= self.limite_minuto:
                logging.info("Aguardando 60 segundos para respeitar o limite de taxa.")
                time.sleep(60)
                self.enviados_no_minuto = 0

            raw_message = self._criar_mensagem(credor, assunto, template, imagem_path)
            if raw_message:
                status, erro = self._enviar_mensagem_com_tentativas(raw_message)
                logs_envio.append((credor.email, status, erro))
                logging.info(f"Email para {credor.email} - Status: {status} - Erro: {erro}")

            self.enviados_no_minuto += 1

        return logs_envio

    def _criar_mensagem(self, credor, assunto, template, imagem_path):
        try:
            message = MIMEMultipart("related")
            message['to'] = credor.email
            message['from'] = self.remetente
            message['subject'] = assunto

            corpo_html = MIMEText(template.format(
                nome=credor.nome,
                classe=credor.classe,
                valor=credor.valor,
                cpf_cnpj=credor.cpf_cnpj,
                endereco=credor.endereco
            ), 'html')
            message.attach(corpo_html)

            with open(imagem_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-ID', '<imagem1>')
                message.attach(img)

            return base64.urlsafe_b64encode(message.as_bytes()).decode()
        except Exception as e:
            logging.error(f"Erro ao criar mensagem para {credor.email}: {e}")
            return None

    def _enviar_mensagem_com_tentativas(self, raw_message):
        for tentativa in range(1, self.tentativas + 1):
            try:
                sent_message = self.service.users().messages().send(
                    userId='me', body={'raw': raw_message}
                ).execute()
                return "Enviado", "N/A"
            except HttpError as error:
                logging.warning(f"Tentativa {tentativa} falhou para envio de email - Erro: {error}")
                if tentativa < self.tentativas:
                    time.sleep(5)  # Pausa entre tentativas
                else:
                    return "Falha", f"Erro após {self.tentativas} tentativas: {error}"
