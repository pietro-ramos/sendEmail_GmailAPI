import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ENV_PATH = Path(__file__).resolve().with_name(".env")


def _load_env_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


if load_dotenv:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    _load_env_fallback(ENV_PATH)

# Configurações de envio de e-mail (Outlook/Graph)
REMETENTE = os.getenv("EMAIL_REMETENTE_OUTLOOK", "admjud@scalzilliaj.com.br")
IMAGEM_PATH = ""  # não usar imagem
ASSUNTO = os.getenv("EMAIL_ASSUNTO_OUTLOOK", "AVISO AOS CREDORES - RECUPERAÇÃO JUDICIAL")

# Configurações de envio via Locaweb API
LOCAWEB_API_URL = os.getenv("LOCAWEB_API_URL", "https://api.smtplw.com.br/v1/messages")
LOCAWEB_API_TOKEN = os.getenv("LOCAWEB_API_TOKEN", "")
REMETENTE_LOCAWEB = os.getenv("EMAIL_REMETENTE_LOCAWEB", REMETENTE)
ASSUNTO_LOCAWEB = os.getenv("EMAIL_ASSUNTO_LOCAWEB", ASSUNTO)

# Configurações de envio via SMTP (provedor genérico)
SMTP_HOST = (
  os.getenv("SMTP_HOST", os.getenv("OPENWEB_TEMP_SMTP_HOST", "")).strip()
)
SMTP_PORT = int(os.getenv("SMTP_PORT", os.getenv("OPENWEB_TEMP_SMTP_PORT", "587")))
SMTP_USERNAME = os.getenv(
  "SMTP_USERNAME",
  os.getenv("OPENWEB_TEMP_SMTP_USERNAME", ""),
).strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", os.getenv("OPENWEB_TEMP_SMTP_PASSWORD", ""))
SMTP_SECURITY = (
  os.getenv("SMTP_SECURITY", os.getenv("OPENWEB_TEMP_SMTP_SECURITY", "none"))
  .strip()
  .lower()
  or "none"
)
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", os.getenv("OPENWEB_TEMP_SMTP_TIMEOUT", "60")))
SMTP_REQUIRE_AUTH = (
  os.getenv(
    "SMTP_REQUIRE_AUTH",
    os.getenv("OPENWEB_TEMP_SMTP_REQUIRE_AUTH", "true"),
  )
  .strip()
  .lower()
  in {"1", "true", "yes", "on"}
)
SMTP_RATE_LIMIT_PER_HOUR = int(
  os.getenv(
    "SMTP_RATE_LIMIT_PER_HOUR",
    os.getenv("OPENWEB_TEMP_RATE_LIMIT_PER_HOUR", "40"),
  )
)
REMETENTE_SMTP = os.getenv("EMAIL_REMETENTE_SMTP", SMTP_USERNAME or REMETENTE)
ASSUNTO_SMTP = os.getenv("EMAIL_ASSUNTO_SMTP", ASSUNTO)

# Configuracoes de envio via Gmail
REMETENTE_GMAIL = os.getenv("EMAIL_REMETENTE_GMAIL", "naoresponda@rdv-insolvencia.com")
IMAGEM_PATH_GMAIL = os.getenv("EMAIL_IMAGEM_GMAIL", "data/Imagem1.png")
ASSUNTO_GMAIL = os.getenv(
    "EMAIL_ASSUNTO_GMAIL",
    "",
)

# Caminho do arquivo Excel (padrão)
ARQUIVO_EMAILS = 'data/direct_lista_cartas.xlsx'
ARQUIVO_EMAILS_LOCAWEB = ''

# Versões alternativas para credores do exterior
ARQUIVO_EMAILS_EXTERIOR = 'data/credores_exterior.xlsx'
ARQUIVO_EMAILS_TANAC_EXTERIOR = 'data/credores_exterior tanac.xlsx'
CLASSE_EXTERIOR = 'CREDOR_EXTERIOR'
ARQUIVO_RELATORIO = 'relatorio_bounces.xlsx'
# Diretório onde ficam os PDFs individuais das cartas (opcional)
CARTAS_DIR = 'data/cartas'

# Configurações Microsoft Graph
TENANT_ID = os.getenv("GRAPH_TENANT_ID", "be8d70b1-1ec7-4a95-b216-be4b9fff02e4")
CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "197f4f0d-69b9-44c6-9c24-6204e6e3063b")
CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")


# Limite padrão do Exchange é ~30 mensagens/minuto; ajuste conforme necessidade
RATE_LIMIT_PER_MIN = 30
RETRIES = 3

# Configurações de captura de bounces
BOUNCE_PROVIDER_DEFAULT = os.getenv("BOUNCE_PROVIDER_DEFAULT", "outlook")
BOUNCE_AFTER_DATE_GMAIL = os.getenv("BOUNCE_AFTER_DATE_GMAIL", "2024-11-01")
BOUNCE_AFTER_DATE_OUTLOOK = os.getenv("BOUNCE_AFTER_DATE_OUTLOOK", "2026-04-30")
ASSUNTO_NDR_OUTLOOK = os.getenv("ASSUNTO_NDR_OUTLOOK", ASSUNTO)
BOUNCE_MAX_MESSAGES = int(os.getenv("BOUNCE_MAX_MESSAGES", "3000"))
BOUNCE_PAGE_SIZE = int(os.getenv("BOUNCE_PAGE_SIZE", "300"))

TEMPLATE_GMAIL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comunicado Importante</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
        }}
        .container {{
            display: table;
            width: 100%;
            height: 100%;
        }}
        .content {{
            display: table-cell;
            vertical-align: middle;
            text-align: center;
            padding: 20px;
        }}
        .bold {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <img src="cid:imagem1" alt="Imagem RDV" /><br><br><br><br>

            <p><strong>À {nome},</strong></p>

            <p>Comunicado Importante:</p>

            <p>A RDV Administração Judicial foi designada como administradora judicial no processo <br>
            de recuperação judicial da MMR Indústria Mecânica (Serra Inox), <br>
            no qual você consta como credor(a).<br>
            Estamos realizando uma verificação dos créditos e contamos <br>
            com a sua colaboração para darmos andamento a esta etapa do processo..</p><br>

            <p><strong>Anexo está um PDF com as informações específicas do seu caso.</strong></p><br><br><br>

            <p><strong>Tire suas dúvidas:<br>
            Whatsapp 51 99918-1288</strong><br>
            Fone 54 3538-6488<br>
            Rua Dr. Montaury, 2090, Sala 1404, Caxias do Sul - RS</p>

            <br><br><br><br>

            <p><strong>DICAS DE SEGURANÇA</strong></p>

            <p>• Não solicitamos dispositivo de segurança (ex: token) para visualização dos comunicados.</p>

            <p>Essa é uma mensagem automática. Por favor, não responda a este e-mail.<br>
            Respeitamos sua <a href="https://rdv-insolvencia.com/privacidade/">privacidade</a>.</p>
        </div>
    </div>
</body>
</html>
"""


# Template para email com anexo PDF
TEMPLATE_PDF = """
<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Aviso aos Credores</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1c1c1c; }}
        p {{ margin: 0 0 12px 0; }}
    </style>
</head>
<body>
    <p>Prezado(a) credor(a),</p>
    <p>Em anexo segue informativo a respeito da respectiva falência.</p>
    <p>Pedimos por gentileza que leia o arquivo com atenção.</p>
    <p>Havendo dúvidas, estamos à disposição pelo WhatsApp 51 99305-0115 (somente mensagens) e pelo e-mail <a href=\"mailto:admjud@scalzilliaj.com.br\">admjud@scalzilliaj.com.br</a>.</p>
    <p>Atenciosamente,<br>
    SCALZILLI, VINHAS & VICENTE ADMINISTRAÇÃO JUDICIAL LTDA.  
    </p>
</body>
</html>
"""

# Template para email sem anexo

TEMPLATE_HTML ="""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Aviso aos Credores</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1c1c1c; margin: 0; padding: 16px; }}
    p {{ margin: 0 0 12px 0; }}
    .bloco {{ margin: 16px 0; padding: 12px; border-left: 4px solid #b0b0b0; background: #f9f9f9; }}
    .pergunta {{ font-weight: bold; }}
    .sim {{ color: #0b7a27; font-weight: bold; }}
    .nao {{ color: #b00020; font-weight: bold; }}
    .link {{ color: #0057b8; text-decoration: none; }}
    .rodape {{ margin-top: 20px; font-size: 0.95em; color: #444; }}
  </style>
</head>
<body>
  <p>Prezado(a) {nome},</p>
  <p>CPF/CNPJ: {cpf_cnpj}<br>


  <div class="bloco">
    <p>Na condição de Administrador Judicial nomeado nos autos do processo n. <strong>0081939-65.2025.8.16.0014</strong>, em trâmite perante a <strong>26ª VARA DE FALÊNCIAS E RECUPERAÇÃO JUDICIAL DE CURITIBA/PR</strong>, comunicamos o deferimento da Recuperação Judicial do <strong>FERRO VELHO BATISTA LTDA. e ARAÚNA ADMINISTRAÇÃO E PARTICIPAÇÃO LTDA</strong>. O pedido de Recuperação Judicial foi protocolado em 18 de novembro de 2025</p>
     <p>O seu crédito foi indicado pela empresa devedora da seguinte forma:</p>
       <strong>Valor: {valor}</strong><br>
       <strong>Classe: {classe}</strong><br>
       <!-- <strong>Natureza: {natureza}</strong><br>
       <strong>Origem: {origem}</p></strong> -->
  </div>

  <p class="pergunta">O VALOR E A CLASSE ESTÃO CORRETOS?</p>

  <p class="sim">SIM</p>
  <p>Então não precisa apresentar divergência de crédito. <strong>Basta responder este e-mail confirmando o valor indicado pelas Recuperandas</strong> e aguardar os demais desdobramentos do processo. Você poderá acompanhar o andamento do processo com as principais informações através do site <a class="link" href="https://scalzilliaj.com.br/" target="_blank">https://scalzilliaj.com.br/</a> ou, se preferir, você também poderá usar os nossos canais de atendimento.</p>

  <p class="nao">NÃO</p>
  <p>No prazo máximo de 15 (quinze) dias, <strong><ins>a contar da publicação do edital do art. 52, § 1º da LREF</strong></ins>, apresente sua divergência através de uma dessas formas:</p>
  <ol style="margin-top: 4px; margin-bottom: 12px;">
    <li>Via e-mail ao endereço eletrônico <a class="link" href="mailto:admjud@scalzilliaj.com.br">admjud@scalzilliaj.com.br</a>; ou</li>
    <li>Via site, por meio do link <a class="link" href="https://scalzilliaj.com.br/habilitacoes-e-divergencias" target="_blank">https://scalzilliaj.com.br/habilitacoes-e-divergencias</a>.</li>
  </ol>
  <p>A sua divergência deverá acompanhar: (i) o valor do crédito atualizado até a data do pedido da Recuperação Judicial <strong>(18 de novembro de 2025)</strong>, sua origem e sua classificação; e (ii) os documentos comprobatórios do crédito.</p>

  <div class="rodape">
    <p><strong>SCZ + B – SCALZILLI E BECUE ADMINISTRAÇÃO JUDICIAL</strong><br>
    Administradora Judicial<br>
    <!-- WhatsApp: (51) 99305-0115 (somente mensagens)<br> -->
    E-mail: <a class="link" href="mailto:contato@sczd.com.br">contato@sczd.com.br</a><br>
    Site: <a class="link" href="https://scalzilliaj.com.br/" target="_blank">https://scalzilliaj.com.br/</a></p>
  </div>
</body>
</html>
"""

TEMPLATE_ABM_TEMP_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Comunicação ao Credor</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background: #ffffff;
      color: #000000;
      font-family: Aptos, Calibri, Arial, sans-serif;
      font-size: 16px;
      line-height: 1.16;
    }}
    .container {{
      max-width: 780px;
      margin: 0 auto;
      background: #ffffff;
    }}
    p {{
      margin: 0 0 11px 0;
      text-align: justify;
    }}
    .espaco {{
      margin-bottom: 22px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <p>Ao(À) Senhor(a) credor(a)</p>
    <p><strong>{nome}</strong></p>
    <p>CPF/CNPJ nº <strong>{cpf_cnpj}</strong></p>
    <p class="espaco">
      Ref.: Recuperação Judicial do Grupo Postos ABM -- Processo nº
      5015739-98.2026.8.21.0019 -- Comunicação ao credor (art. 22, I, "a", da Lei nº
      11.101/2005).
    </p>
    <p>Prezado(a) Senhor(a),</p>
    <p>
      Na qualidade de Administradora Judicial nomeada nos autos da recuperação judicial em epígrafe,
      cujo processamento foi deferido em 22/06/2026, comunicamos a V. Sa., para os fins do art. 22,
      inciso I, alínea "a", da Lei nº 11.101/2005, que o pedido de recuperação judicial foi ajuizado
      em 04/06/2026, data que serve de base à atualização dos créditos (art. 9º, II, da Lei nº
      11.101/2005).
    </p>
    <p>
      Comunicamos, ainda, que o crédito de V. Sa. foi assim relacionado pela recuperanda, quanto à
      natureza, ao valor e à classificação:
    </p>
    <p><strong>{valor_html}</strong></p>
    <p>
      Caso V. Sa. discorde da natureza, do valor ou da classificação acima indicados, poderá
      apresentar habilitação ou divergência diretamente a esta Administração Judicial no prazo de
      15 (quinze) dias contado da publicação do edital previsto no art. 52, § 1º, da Lei nº
      11.101/2005 (art. 7º, § 1º), instruída com os documentos comprobatórios, pelo e-mail
      contato@poaj.com.br ou no endereço ao final indicado.
    </p>
    <p>
      Esta comunicação tem caráter meramente informativo e individual, não substituindo o edital de
      que trata o art. 52, § 1º, tampouco o relativo à relação de credores (art. 7º, § 2º), cujos
      prazos e efeitos legais permanecem íntegros.
    </p>
    <p>
      Se o crédito informado estiver correto, não há necessidade de confirmação por parte do
      credor, sendo suficiente aguardar os demais andamentos do processo.
    </p>
    <p>
      O andamento processual e as principais informações relativas ao feito poderão ser
      acompanhados por meio do site www.poaj.com.br.
    </p>
    <p class="espaco">Atenciosamente,</p>
    <p>Pozzobon &amp; Oliveira Administração Judicial Ltda.</p>
  </div>
</body>
</html>
"""
