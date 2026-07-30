# Disparador de comunicados por e-mail

Aplicação local para envio de comunicados com PDF individual obrigatório. O
mesmo lote pode ser processado por Outlook/Microsoft Graph, Gmail API ou um
servidor SMTP genérico. Outlook permanece como provedor padrão.

## Funcionalidades

- envio principal por Outlook/Microsoft Graph;
- envio alternativo pela API oficial do Gmail;
- SMTP configurável, com TLS/SSL, autenticação, timeout, limite por janela,
  tentativas e intervalo entre retries;
- localização do PDF por CPF/CNPJ e classe do credor;
- anexos adicionais com sufixos `_2`, `_3` e seguintes;
- relatório Excel com o resultado de cada destinatário;
- captura de bounces no Outlook e no Gmail, atualizando o relatório de envio.

O fluxo exige PDF. Campanhas sem anexo, credores do exterior, Locaweb e
templates temporários não fazem parte desta base.

## Estrutura

```text
main.py                    ponto de entrada dos envios
main_bounces.py            captura e conciliação de bounces
config.py                  leitura e validação das variáveis de ambiente
app/                       seleção e execução dos provedores
models/                    modelo de credor
services/
  auth.py                  OAuth do Gmail
  gmail_email.py           envio pela Gmail API
  graph_auth.py            autenticação Microsoft Graph
  graph_email.py           envio pelo Outlook
  smtp_email.py            envio SMTP
  pdf_files.py             localização compartilhada dos PDFs
  bounce_*.py              captura e conciliação de bounces
util/input_excel.py        leitura da planilha
tests/                     testes sem acesso a provedores reais
```

## Instalação

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o `.env` e mantenha fora do Git todos os tokens, credenciais,
planilhas, PDFs e relatórios.

## Entrada e PDFs

A planilha deve possuir:

- nome do credor;
- e-mail;
- CPF ou CNPJ;
- classe, quando fizer parte do nome do PDF;
- opcionalmente valor, endereço, natureza e origem.

Os aliases mais comuns são aceitos, por exemplo `Nome do Credor`, `E-mail`,
`CPF/CNPJ` e `Classe`.

O PDF é procurado nesta ordem:

```text
<documento>_<classe>.pdf
<documento>_<classe>_2.pdf
<documento>_<classe>_3.pdf
<documento>.pdf
```

CPF/CNPJ é comparado apenas por dígitos. A classe é normalizada sem acentos e
com `_` no lugar de pontuação. O alias legado `QUIROGRAF_RIO` continua aceito.

## Provedores

Selecione um valor em `PROVEDOR_ENVIO`:

| Valor | Integração | Configuração essencial |
|---|---|---|
| `outlook` | Microsoft Graph | remetente, tenant, client ID e client secret |
| `gmail` | Gmail API | remetente, `credentials.json` e token OAuth |
| `smtp` | SMTP genérico | host, porta, remetente, segurança e credenciais |

Executar o lote:

```powershell
.\.venv\Scripts\python.exe main.py
```

O Gmail abre o navegador no primeiro consentimento OAuth e grava o token no
caminho configurado. O SMTP usa `starttls` por padrão; `auto` escolhe SSL na
porta 465 e STARTTLS nas demais portas. O modo `none` deve ser usado somente
quando a infraestrutura exigir explicitamente uma conexão sem TLS.

### Limites e retries do SMTP

Exemplo de 40 mensagens por hora, com três tentativas e cinco segundos entre
tentativas:

```dotenv
SMTP_RATE_LIMIT=40
SMTP_RATE_WINDOW_SECONDS=3600
SMTP_RETRIES=3
SMTP_RETRY_DELAY_SECONDS=5
```

Os códigos temporários `421`, `450`, `451` e `452`, além de falhas de conexão,
podem gerar nova tentativa. Erros SMTP definitivos não são repetidos.

## Bounces

O arquivo indicado em `BOUNCE_REPORT_FILE` deve ser o relatório gerado pelo
envio. Escolha `outlook` ou `gmail` em `BOUNCE_PROVIDER` e execute:

```powershell
.\.venv\Scripts\python.exe main_bounces.py
```

O processo busca retornos posteriores à data configurada, cruza o
destinatário com linhas marcadas como `Enviado` e altera as correspondências
para `Falha`, registrando o motivo. O token de leitura do Gmail usa arquivo
separado por ter escopo OAuth diferente do token de envio.

## Validação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app models services util main.py main_bounces.py
```

Os testes não enviam mensagens nem consultam caixas reais.

## Segurança operacional

- nunca versione `.env`, `credentials*.json`, `token*.json`, planilhas ou PDFs;
- use o menor escopo possível nas aplicações Microsoft e Google;
- valide o lote e os PDFs antes de executar;
- teste SMTP com uma conta e uma janela pequenas antes de ampliar o volume;
- preserve o relatório de envio, pois ele é a base da conciliação de bounces.
