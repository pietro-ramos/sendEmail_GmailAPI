# Configuracao Do Ambiente

O sistema combina configuracoes em codigo com variaveis de ambiente.

## Dependencias

Crie ou atualize a virtualenv:

```powershell
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Dependencias principais:

- `pandas`: leitura e escrita de Excel.
- `openpyxl`: engine para arquivos `.xlsx`.
- `XlsxWriter`: escrita de relatorios com multiplas abas.
- `requests`: chamadas HTTP para Graph e Locaweb.
- `msal`: autenticacao Microsoft Graph.
- `google-api-python-client` e `google-auth-oauthlib`: Gmail API.

## Variaveis De Ambiente

O arquivo `.env.example` lista as variaveis esperadas. O projeto carrega `.env` automaticamente via `python-dotenv` quando as dependencias de `requirements.txt` estao instaladas. O carregamento usa `override=True`; portanto, se a mesma chave existir no sistema operacional e no `.env`, o valor do `.env` prevalece.

### Microsoft Graph

- `GRAPH_TENANT_ID`: tenant da organizacao.
- `GRAPH_CLIENT_ID`: client id do app registrado no Azure.
- `GRAPH_CLIENT_SECRET`: segredo do app.
- `EMAIL_REMETENTE_OUTLOOK`: caixa usada como remetente.
- `EMAIL_ASSUNTO_OUTLOOK`: assunto padrao para envios Outlook.

### Gmail

- `EMAIL_REMETENTE_GMAIL`: remetente usado na mensagem.
- `EMAIL_ASSUNTO_GMAIL`: assunto padrao para envios Gmail.
- `EMAIL_IMAGEM_GMAIL`: caminho da imagem inline, se usada.

Tambem sao necessarios:

- `credentials.json`: arquivo OAuth do Google Cloud.
- `token.json`: gerado apos autorizacao local.

Esses arquivos nao devem ser versionados.

### Locaweb

- `LOCAWEB_API_TOKEN`: token de API.
- `LOCAWEB_API_URL`: endpoint da API.
- `EMAIL_REMETENTE_LOCAWEB`: remetente.
- `EMAIL_ASSUNTO_LOCAWEB`: assunto padrao.

### Devolucoes (Bounces)

- `BOUNCE_PROVIDER_DEFAULT`: `outlook` ou `gmail`.
- `BOUNCE_AFTER_DATE_GMAIL`: data de corte para Gmail, formato `YYYY-MM-DD`.
- `BOUNCE_AFTER_DATE_OUTLOOK`: data de corte para Outlook, formato `YYYY-MM-DD`.
- `ASSUNTO_NDR_OUTLOOK`: assunto de referencia para devolucoes Outlook.
- `BOUNCE_MAX_MESSAGES`: limite maximo de mensagens analisadas.
- `BOUNCE_PAGE_SIZE`: tamanho de pagina nas consultas.

## Configuracao Funcional

O arquivo `config.py` define defaults funcionais:

- remetentes;
- assuntos;
- caminhos das planilhas;
- caminho de cartas/PDFs;
- templates HTML;
- limites de taxa;
- parametros de devolucoes.

O arquivo `main.py` define o comunicado ativo no bloco:

```python
PROVEDOR_ENVIO = (os.getenv("PROVEDOR_ENVIO") or "outlook").strip().lower()
ARQUIVO_PLANILHA = ARQUIVO_EMAILS
ENVIAR_COM_PDF = True
USAR_LISTA_EXTERIOR = False
USAR_BUSCA_PDF_EXTERIOR = False
```

O ponto de entrada `main.py` permanece restrito ao fluxo padrao `outlook`. O
modulo ABM temporario usa `main_gmail_temp_preview.py` e
`main_openweb_temp.py`; consulte `data/temp/GUIA_MODULO_TEMP_ABM.md`.

Campos opcionais para sobrescrever sem alterar `config.py`:

```python
ASSUNTO_CUSTOM = ""
TEMPLATE_CUSTOM = ""
REMETENTE_CUSTOM = ""
IMAGEM_CUSTOM = ""
```

## Recomendacao Para Equipe

Para trabalho em equipe, evite depender de edicoes frequentes em `config.py`. O caminho recomendado para evolucao e criar configuracoes por comunicado ou mala direta, por exemplo:

```text
configs/
  edumax.yaml
  fastsystem.yaml
  rodomak.yaml
```

Enquanto isso nao existir, registre no PR qual comunicado foi configurado e revise manualmente o bloco de `main.py`.

## Arquivos Que Nao Devem Ir Para Git

- `data/`
- `*.xlsx`
- `credentials.json`
- `token.json`
- `.env`
- `email_log.log`
- arquivos de depuracao com corpos de e-mail
- PDFs reais de credores
