# Operacao De Envio

Este guia descreve o uso operacional do sistema.

## 1. Preparar O Comunicado

Escolha a empresa/lista de credores e separe:

- planilha `.xlsx` de credores;
- PDFs individuais, se o envio exigir anexo;
- assunto do e-mail;
- template HTML correto;
- provedor de envio;
- remetente autorizado.

Coloque os arquivos operacionais na area local esperada, normalmente:

```text
data/
data/cartas/
```

Esses arquivos nao devem ser commitados.

## 2. Configurar Ambiente

Configure as variaveis de ambiente do provedor escolhido.

Exemplo para Outlook em PowerShell:

```powershell
$env:GRAPH_TENANT_ID = "..."
$env:GRAPH_CLIENT_ID = "..."
$env:GRAPH_CLIENT_SECRET = "..."
$env:EMAIL_REMETENTE_OUTLOOK = "admjud@scalzilliaj.com.br"
$env:EMAIL_ASSUNTO_OUTLOOK = "AVISO AOS CREDORES - ..."
```

## 3. Ajustar O Comunicado

Em `main.py`, configure:

```python
PROVEDOR_ENVIO = (os.getenv("PROVEDOR_ENVIO") or "outlook").strip().lower()
ARQUIVO_PLANILHA = ARQUIVO_EMAILS
ENVIAR_COM_PDF = True
USAR_LISTA_EXTERIOR = False
USAR_BUSCA_PDF_EXTERIOR = False
```

Neste ponto de entrada, o provedor valido e `outlook`. O envio ABM temporario
foi isolado em `main_gmail_temp_preview.py` e `main_openweb_temp.py`; consulte
`data/temp/GUIA_MODULO_TEMP_ABM.md`.

Se precisar sobrescrever assunto, template, remetente ou imagem apenas para uma execucao:

```python
ASSUNTO_CUSTOM = "..."
TEMPLATE_CUSTOM = "..."
REMETENTE_CUSTOM = "..."
IMAGEM_CUSTOM = "..."
```

## 4. Executar

```powershell
.\.venv\Scripts\python.exe main.py
```

Durante a execucao, o sistema imprime a quantidade de credores carregados e o provedor usado.

## 5. Resultado

O envio gera uma lista de resultados com:

- `Destinatario`
- `Status do envio`
- `Erro`

Essa lista e salva por `services.relatorio.Relatorio` em `ARQUIVO_RELATORIO`, configurado em `config.py`.

## Comportamento Por Provedor

### Outlook

Usa Microsoft Graph. Para cada credor:

1. limpa espacos do e-mail;
2. formata valor em BRL quando aplicavel;
3. preenche o template;
4. anexa PDFs em base64;
5. envia para `/sendMail`.

Se `ENVIAR_COM_PDF=True` e nenhum PDF for encontrado, a mensagem nao e enviada.

### Gmail

Usa Gmail API com OAuth local. Para cada credor:

1. cria `EmailMessage`;
2. define `To`, `From` e `Subject`;
3. adiciona texto simples e HTML;
4. adiciona imagem inline se existir;
5. adiciona PDFs encontrados;
6. envia mensagem como `raw` base64.

No fluxo Gmail atual, ausencia de PDF gera aviso em log, mas nao bloqueia necessariamente a montagem da mensagem.

### Locaweb

Monta um MIME multipart e envia pela API Locaweb. Se `ENVIAR_COM_PDF=True` e nenhum PDF for encontrado, a montagem falha para aquele credor.

## Limite De Taxa E Tentativas

Configuracoes em `config.py`:

```python
RATE_LIMIT_PER_MIN = 30
RETRIES = 3
```

Outlook e Locaweb respeitam esses valores no servico. Gmail usa limites internos definidos em `services/send_email.py`.

## Checklist Antes De Enviar

- Ambiente virtual instalado.
- Variaveis do provedor configuradas.
- Remetente autorizado.
- Planilha correta selecionada.
- Assunto revisado.
- Template revisado.
- `ENVIAR_COM_PDF` coerente com o comunicado.
- PDFs conferidos.
- Teste feito com uma planilha pequena antes do envio final.
- Arquivos sensiveis fora do Git.

## Reexecucao

Para reexecutar um comunicado, salve ou renomeie o relatorio anterior antes de rodar novamente, porque `ARQUIVO_RELATORIO` pode ser sobrescrito.
