import base64
import time
import logging
import os
import mimetypes
from email.message import EmailMessage
from googleapiclient.errors import HttpError
from services.email_template import renderizar_template_email
from util.input_excel import gerar_nomes_candidatos_carta


class EmailService:
    def __init__(
        self,
        service,
        remetente,
        cartas_dir=None,
        require_pdf=True,
        rate_limit_per_min=150,
        retries=3,
    ):
        self.service = service
        self.remetente = remetente
        self.enviados_no_minuto = 0
        self.limite_minuto = rate_limit_per_min
        self.tentativas = retries
        self.require_pdf = require_pdf

        # Diretório de cartas individuais (PDFs)
        self.cartas_dir = cartas_dir or (
            os.path.join("data", "cartas") if self.require_pdf else ""
        )
        if self.cartas_dir and not os.path.exists(self.cartas_dir):
            os.makedirs(self.cartas_dir)
            logging.info(f"Diretório {self.cartas_dir} criado")
        elif self.cartas_dir:
            logging.info(f"Arquivos encontrados em {self.cartas_dir}: {os.listdir(self.cartas_dir)}")

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
                logs_envio.append({
                    'Destinatario': credor.email,
                    'Status do envio': status,
                    'Erro': erro
                })
                logging.info(f"Email para {credor.email} - Status: {status} - Erro: {erro}")
            else:
                logs_envio.append({
                    'Destinatario': credor.email,
                    'Status do envio': 'Falha',
                    'Erro': 'Erro ao criar a mensagem'
                })
                logging.error(f"Falha ao criar mensagem para {credor.email}")

            self.enviados_no_minuto += 1

        return logs_envio

    def _criar_mensagem(self, credor, assunto, template, imagem_path):
        """Cria a mensagem com corpo HTML, imagem inline e PDF anexo."""
        try:
            message = EmailMessage()

            message['To'] = credor.email
            message['From'] = self.remetente
            message['Subject'] = assunto

            # Formatar o template HTML com os dados do credor
            corpo_html = renderizar_template_email(template, credor)

            # Texto simples (fallback)
            texto_plano = (
                f"Prezado(a) {credor.nome}, comunicado importante em anexo."
                if self.require_pdf
                else f"Prezado(a) {credor.nome}, comunicado importante no corpo deste email."
            )
            message.set_content(texto_plano)

            # HTML
            message.add_alternative(corpo_html, subtype='html')

            # Imagem inline (cid:imagem1)
            imagem_path_norm = os.path.normpath(imagem_path) if imagem_path else ""
            if imagem_path_norm and os.path.isfile(imagem_path_norm):
                with open(imagem_path_norm, 'rb') as img_file:
                    img_data = img_file.read()
                    content_type, _ = mimetypes.guess_type(imagem_path_norm)
                    if content_type is None:
                        content_type = 'image/png'
                    maintype, subtype = content_type.split('/', 1)
                    message.add_attachment(
                        img_data,
                        maintype=maintype,
                        subtype=subtype,
                        cid='imagem1',
                        disposition='inline',
                        filename=os.path.basename(imagem_path_norm)
                    )
                logging.info(f"Imagem anexada: {imagem_path_norm}")
            elif imagem_path_norm:
                logging.warning(f"Imagem não encontrada: {imagem_path_norm}")

            # Anexar PDF(s) do credor (<CNPJ>_<CLASSE>.pdf e variantes _2, _3, ...)
            pdf_attachment_ok = False
            candidatos = (
                gerar_nomes_candidatos_carta(
                    credor.nome,
                    credor.cpf_cnpj,
                    credor.classe,
                )
                if self.cartas_dir
                else []
            )
            logging.info(f"Candidatos PDF para {credor.nome}: {candidatos}")
            for filename in candidatos:
                pdf_path = os.path.normpath(os.path.join(self.cartas_dir, filename))
                if not os.path.exists(pdf_path):
                    continue
                # Anexa o arquivo principal
                base_name, ext = os.path.splitext(filename)
                all_pdfs = [pdf_path]
                # Busca sufixos numéricos: _2.pdf, _3.pdf, ...
                idx = 2
                while True:
                    extra = os.path.normpath(os.path.join(self.cartas_dir, f"{base_name}_{idx}{ext}"))
                    if not os.path.exists(extra):
                        break
                    all_pdfs.append(extra)
                    idx += 1

                for i, p in enumerate(all_pdfs):
                    file_size = os.path.getsize(p)
                    if file_size == 0:
                        logging.warning(f"Arquivo PDF vazio: {p} (0 bytes)")
                        continue
                    with open(p, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                        if i == 0:
                            display_name = f"Comunicado - {credor.nome}.pdf"
                        else:
                            display_name = f"Comunicado - {credor.nome} ({i + 1}).pdf"
                        message.add_attachment(
                            pdf_data,
                            maintype='application',
                            subtype='pdf',
                            filename=display_name
                        )
                        logging.info(f"PDF anexado: {display_name} ({file_size} bytes)")
                        pdf_attachment_ok = True
                break

            if not pdf_attachment_ok:
                mensagem = f"PDF obrigatorio ausente para {credor.nome}. Candidatos: {candidatos}"
                if self.require_pdf:
                    logging.error(mensagem)
                    return None
                logging.warning(mensagem)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            return encoded_message

        except Exception as e:
            logging.error(f"Erro ao criar mensagem para {credor.email}: {str(e)}", exc_info=True)
            return None

    def _find_similar_pdf_files(self, nome):
        """Encontra arquivos PDF com nomes semelhantes ao nome do credor."""
        if not os.path.exists(self.cartas_dir):
            return []
        nome_lower = nome.lower().replace(' ', '')
        return [
            filename
            for filename in os.listdir(self.cartas_dir)
            if filename.lower().endswith('.pdf') and nome_lower in filename.lower().replace('_', '')
        ]

    def _enviar_mensagem_com_tentativas(self, raw_message):
        for tentativa in range(1, self.tentativas + 1):
            try:
                sent_message = self.service.users().messages().send(
                    userId='me', body={'raw': raw_message}
                ).execute()
                return "Enviado", "N/A"
            except HttpError as error:
                erro_msg = f"Erro HTTP: {str(error)}"
                logging.warning(f"Tentativa {tentativa} falhou - {erro_msg}")
                if tentativa < self.tentativas:
                    time.sleep(5)
                else:
                    return "Falha", f"Erro após {self.tentativas} tentativas: {erro_msg}"
            except Exception as error:
                erro_msg = f"Erro desconhecido: {str(error)}"
                logging.error(erro_msg)
                return "Falha", erro_msg
