# sendEmail_GmailAPI

> Sistema interno para mala direta de comunicados a credores em recuperacao judicial, falencia e processos relacionados. Usado operacionalmente para ler planilhas por empresa/lista de credores, montar e-mails com templates HTML, anexar cartas individuais em PDF, enviar por Outlook/Microsoft Graph, Gmail API ou Locaweb, e atualizar relatorios com resultados e devolucoes (bounces).

---

## Stack

| Tecnologia | Versao |
|---|---|
| Python | 3.13.5 no ambiente local atual |
| pandas | `>=2.2.0` |
| openpyxl | `>=3.1.5` |
| XlsxWriter | `>=3.2.0` |
| requests | `>=2.31.0` |
| msal | `>=1.30.0` |
| google-api-python-client | `>=2.149.0` |
| google-auth-oauthlib | `>=1.2.1` |

Nao ha framework web. O projeto e um conjunto de scripts Python para execucao local/operacional.

---

## Nomenclatura Do Projeto

| Termo | Uso no projeto |
|---|---|
| Comunicado | Execucao operacional de uma mala direta para uma empresa/lista de credores. |
| Mala direta | Envio em massa de comunicados individualizados para credores. |
| Lista de credores | Planilha `.xlsx` com destinatarios e dados usados no template. |
| Credor | Registro individual carregado da planilha. |
| Carta/PDF | Documento individual anexado ao e-mail do credor. |
| Provedor de envio | Integracao usada para enviar o comunicado: Outlook/Microsoft Graph, Gmail API, Locaweb ou um SMTP temporario isolado. |
| Devolucao (bounce) | Falha posterior de entrega, capturada para atualizar o relatorio operacional. |
| Relatorio operacional | Arquivo Excel com o resultado do envio e, quando processado, as devolucoes. |

Evite termos de marketing como campanha, lead, prospect, newsletter ou disparo promocional. O contexto do sistema e juridico-operacional: comunicados e mala direta de credores.

---

## Pre-requisitos

- Python instalado e acessivel via `py` ou pela virtualenv local.
- Dependencias instaladas com `requirements.txt`.
- Acesso ao provedor que sera usado no envio do comunicado:
  - Microsoft Graph/Outlook, ou
  - Gmail API, ou
  - Locaweb API, ou
  - Openweb SMTP temporario.
- Planilha `.xlsx` da empresa/lista de credores em formato compativel.
- PDFs individuais em `data/cartas`, quando o comunicado exigir anexo.
- Permissao para usar o remetente configurado.
- Variaveis de ambiente do provedor configuradas antes da execucao.

Arquivos operacionais e sensiveis nao devem ser versionados:

- `data/`
- `*.xlsx`
- `credentials.json`
- `token.json`
- `.env`
- `email_log.log`
- relatorios reais de envios
- PDFs reais de credores

---

## Como Rodar Localmente

```powershell
# 1. Clone
git clone <url-do-repositorio>
cd sendEmail_GmailAPI

# 2. Crie a virtualenv, se ainda nao existir
py -m venv .venv

# 3. Instale dependencias
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Configure as variaveis de ambiente no terminal, na IDE ou no ambiente do usuario.

O arquivo `.env.example` e uma referencia dos nomes esperados. Crie um `.env` local com esses nomes; o projeto carrega esse arquivo automaticamente via `python-dotenv` quando as dependencias de `requirements.txt` estao instaladas.

Exemplo para Outlook/Microsoft Graph:

```powershell
$env:GRAPH_TENANT_ID = "00000000-0000-0000-0000-000000000000"
$env:GRAPH_CLIENT_ID = "00000000-0000-0000-0000-000000000000"
$env:GRAPH_CLIENT_SECRET = "valor-secreto"
$env:EMAIL_REMETENTE_OUTLOOK = "remetente@empresa.com.br"
$env:EMAIL_ASSUNTO_OUTLOOK = "AVISO AOS CREDORES - NOME DO COMUNICADO"
```

Depois ajuste o bloco do comunicado em `main.py` e, se quiser trocar o provedor sem editar o arquivo, use `PROVEDOR_ENVIO`:

```python
PROVEDOR_ENVIO = (os.getenv("PROVEDOR_ENVIO") or "outlook").strip().lower()
ARQUIVO_PLANILHA = ARQUIVO_EMAILS
ENVIAR_COM_PDF = True
USAR_LISTA_EXTERIOR = False
USAR_BUSCA_PDF_EXTERIOR = False

ASSUNTO_CUSTOM = ""
TEMPLATE_CUSTOM = ""
REMETENTE_CUSTOM = ""
IMAGEM_CUSTOM = ""
```

Execute o envio:

```powershell
.\.venv\Scripts\python.exe main.py
```

O envio ABM temporario por Gmail/Openweb usa pontos de entrada separados. Consulte
`data/temp/GUIA_MODULO_TEMP_ABM.md`; ele nao deve ser ativado por `main.py`.

---

## Variaveis De Ambiente

Copie `.env.example` apenas como referencia. Preencha as variaveis conforme o provedor usado no envio do comunicado.

| Variavel | Obrigatoria | Descricao | Exemplo |
|---|---|---|---|
| `GRAPH_TENANT_ID` | Sim para Outlook | Tenant do Microsoft Entra/Azure AD usado pelo Microsoft Graph. | `00000000-0000-0000-0000-000000000000` |
| `GRAPH_CLIENT_ID` | Sim para Outlook | Client ID do app registrado para envio via Graph. | `00000000-0000-0000-0000-000000000000` |
| `GRAPH_CLIENT_SECRET` | Sim para Outlook | Segredo do app usado para obter token. | `valor-secreto` |
| `EMAIL_REMETENTE_OUTLOOK` | Sim para Outlook | Caixa remetente usada no endpoint `/sendMail`. | `remetente@empresa.com.br` |
| `EMAIL_ASSUNTO_OUTLOOK` | Nao | Assunto padrao do envio Outlook. Pode ser sobrescrito em `main.py`. | `AVISO AOS CREDORES - NOME DO COMUNICADO` |
| `PROVEDOR_ENVIO` | Nao | Provedor usado em `main.py`. O ponto de entrada padrao aceita `outlook`. | `outlook` |
| `OPENWEB_TEMP_SMTP_HOST` | Sim para Openweb temporario | Servidor SMTP da conta temporaria. | `mail.seudominio.com.br` |
| `OPENWEB_TEMP_SMTP_USERNAME` | Sim para Openweb temporario | Usuario SMTP, normalmente o e-mail completo. | `nomedeusuario@seudominio.com.br` |
| `OPENWEB_TEMP_SMTP_PASSWORD` | Sim para Openweb temporario | Senha SMTP da conta temporaria. | `valor-secreto` |
| `TEMP_ABM_ASSUNTO` | Nao | Assunto comum ao teste Gmail e ao lote Openweb ABM. | `Comunicacao ao Credor - Grupo Postos ABM` |
| `TEMP_ABM_GMAIL_TEST_DESTINATARIO` | Sim para teste Gmail ABM | Unico destinatario permitido no teste. | `teste@gmail.com` |
| `EMAIL_REMETENTE_GMAIL` | Sim para Gmail | Remetente usado na mensagem Gmail. | `naoresponda@empresa.com.br` |
| `EMAIL_ASSUNTO_GMAIL` | Nao | Assunto padrao do envio Gmail. | `Comunicado Importante - Credores` |
| `EMAIL_IMAGEM_GMAIL` | Nao | Caminho da imagem inline usada pelo template Gmail. | `data/Imagem1.png` |
| `LOCAWEB_API_TOKEN` | Sim para Locaweb | Token da API Locaweb. | `token-secreto` |
| `LOCAWEB_API_URL` | Sim para Locaweb | Endpoint da API de envio. | `https://api.smtplw.com.br/v1/messages` |
| `EMAIL_REMETENTE_LOCAWEB` | Sim para Locaweb | Remetente usado na API Locaweb. | `remetente@empresa.com.br` |
| `EMAIL_ASSUNTO_LOCAWEB` | Nao | Assunto padrao do envio Locaweb. | `AVISO AOS CREDORES - NOME DO COMUNICADO` |
| `BOUNCE_PROVIDER_DEFAULT` | Nao | Provedor usado por `main_bounces.py` para buscar devolucoes. | `outlook` |
| `BOUNCE_AFTER_DATE_GMAIL` | Nao | Data de corte para busca de devolucoes no Gmail. | `2024-11-01` |
| `BOUNCE_AFTER_DATE_OUTLOOK` | Nao | Data de corte para busca de devolucoes no Outlook. | `2026-04-30` |
| `ASSUNTO_NDR_OUTLOOK` | Nao | Assunto de referencia para buscar devolucoes Outlook. Se vazio, usa o assunto Outlook. | `AVISO AOS CREDORES - NOME DO COMUNICADO` |
| `BOUNCE_MAX_MESSAGES` | Nao | Limite maximo de mensagens analisadas na captura de devolucoes. | `3000` |
| `BOUNCE_PAGE_SIZE` | Nao | Tamanho de pagina usado nas consultas de devolucoes. | `300` |

Observacao: `config.py` ainda possui alguns defaults para manter o fluxo local legado funcionando. Para uso em equipe, prefira configurar valores por variavel de ambiente e revisar `main.py` antes da execucao.

---

## Como Testar

Ainda nao ha suite automatizada de testes unitarios ou de integracao versionada no projeto.

Validacao minima recomendada antes de abrir PR:

```powershell
.\.venv\Scripts\python.exe -m compileall app models services util main.py main_bounces.py log_report.py bounce_debug_gmail.py
```

Validacao operacional recomendada antes de envio real:

- Rodar com uma planilha pequena de teste.
- Confirmar que a planilha configurada existe.
- Confirmar que os PDFs esperados existem quando `ENVIAR_COM_PDF=True`.
- Conferir assunto, remetente e template.
- Conferir o relatorio gerado antes de processar devolucoes.

---

## Deploy / Ambientes

| Ambiente | URL | Como fazer deploy |
|---|---|---|
| Local | Nao se aplica | Execucao manual via scripts Python. |
| Desenvolvimento | A confirmar | A confirmar. |
| Producao | Nao ha deploy confirmado | Projeto usado como automacao/script operacional local ate a finalizacao da reestruturacao. |

Nao foi identificado, no codigo atual, pipeline de CI/CD, ambiente hospedado ou processo de deploy automatizado.

---

## Dono / Contato

| Campo | Valor |
|---|---|
| Time responsavel | A confirmar |
| Contato principal | A confirmar |
| Onde abrir issue | A confirmar |

Esses campos devem ser preenchidos antes de publicar o repositorio privado como referencia oficial da equipe.

---

## Uso

### Envio Do Comunicado

```powershell
.\.venv\Scripts\python.exe main.py
```

Saida esperada no console:

```text
Carregados <N> credores do arquivo <planilha>
Iniciando envio via <provedor> para <N> credores...
Envio de e-mails concluido
Relatorio de bounces salvo em '<arquivo_relatorio>'.
```

Apesar da mensagem atual mencionar "bounces", esse relatorio e o relatorio operacional de envio. O processamento de devolucoes acontece em outro script.

### Processar Devolucoes (Bounces)

```powershell
.\.venv\Scripts\python.exe main_bounces.py
```

Esse comando busca devolucoes no provedor configurado e atualiza `ARQUIVO_RELATORIO`.

### Depurar Devolucoes Gmail Sem Destinatario

```powershell
.\.venv\Scripts\python.exe bounce_debug_gmail.py
```

Usa `emails_sem_destinatario.txt` como entrada e gera `corpos_emails_para_analise.txt`.

### Gerar Excel A Partir Do Log

```powershell
.\.venv\Scripts\python.exe log_report.py
```

Le `email_log.log` e gera `email_log.xlsx` com abas de envios e erros, quando houver registros compativeis.

---

## Dependencias Externas

| Servico | Finalidade |
|---|---|
| Microsoft Graph | Envio Outlook e captura de devolucoes Outlook. |
| Gmail API | Envio Gmail, captura de devolucoes Gmail e depuracao de mensagens sem destinatario. |
| Locaweb API | Envio por API Locaweb. |
| Openweb SMTP temporario | Envio SMTP temporario isolado do fluxo padrao. |
| Arquivos Excel locais | Entrada de credores por empresa/lista de credores. |
| PDFs locais em `data/cartas` | Cartas individuais anexadas aos e-mails. |

---

## Estrutura Do Projeto

| Caminho | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada do envio do comunicado. |
| `main_bounces.py` | Ponto de entrada para captura e aplicacao de devolucoes. |
| `bounce_debug_gmail.py` | Apoio para investigar devolucoes Gmail sem destinatario identificado. |
| `log_report.py` | Conversao do log textual para Excel. |
| `config.py` | Defaults funcionais, caminhos, assuntos, templates e configuracoes de provedores. |
| `app/` | Orquestracao da execucao do comunicado. |
| `models/` | Modelos de dominio, hoje `Credor`. |
| `services/` | Integracoes de envio, autenticacao, devolucoes e relatorios. |
| `util/` | Leitura de Excel e regras de normalizacao de nomes de PDFs. |
| `docs/` | Documentacao complementar. |
| `data/` | Dados operacionais locais; nao versionar. |

---

## Fluxo Operacional

1. Escolher a empresa/lista de credores.
2. Separar a planilha `.xlsx` e os PDFs correspondentes.
3. Configurar variaveis de ambiente do provedor.
4. Revisar `config.py` e o bloco do comunicado em `main.py`.
5. Executar `main.py`.
6. Conferir `ARQUIVO_RELATORIO` e `email_log.log`.
7. Executar `main_bounces.py`, se houver necessidade de marcar devolucoes.
8. Arquivar relatorios localmente conforme o fluxo interno da equipe.

---

## Planilhas E PDFs

Cada `.xlsx` em `data/` representa uma empresa, lista de credores ou mala direta de comunicados. O carregador aceita diferentes nomes de coluna para acomodar listas recebidas em formatos variados.

Colunas obrigatorias:

- nome do credor: `Nome do Credor`, `Nome Credor`, `Nome`, `Razao Social/Nome`;
- e-mail: `Email`, `E-mail`, `E-MAIL`, `Email Principal`;
- documento: `CPF / CNPJ`, `CPF/CNPJ`, `CPF`, `CNPJ/CPF`, `CNPJ / CPF`.

Colunas opcionais usadas por templates:

- `Classe`
- `Valor`
- `Endereco`
- `Natureza`
- `Origem`
- `Moeda`

Regra principal dos PDFs nacionais:

```text
<CPF_CNPJ_APENAS_DIGITOS>_<CLASSE_NORMALIZADA>.pdf
<CPF_CNPJ_APENAS_DIGITOS>.pdf
```

Tambem sao aceitos sufixos numericos:

```text
01140047000113_ME_EPP_2.pdf
01140047000113_ME_EPP_3.pdf
```

Mais detalhes: [docs/03-planilhas-e-pdfs.md](docs/03-planilhas-e-pdfs.md).

---

## Documentacao Complementar

- [Visao geral e arquitetura](docs/01-visao-geral.md)
- [Configuracao do ambiente](docs/02-configuracao.md)
- [Planilhas e PDFs esperados](docs/03-planilhas-e-pdfs.md)
- [Operacao de envio](docs/04-operacao-envio.md)
- [Devolucoes, logs e relatorios](docs/05-bounces-e-relatorios.md)
- [Desenvolvimento em equipe](docs/06-desenvolvimento-e-equipe.md)

---

## Pendencias De Confirmacao

Para finalizar o README sem campos "A confirmar", ainda faltam informacoes que nao estao no codigo:

- URL oficial do repositorio privado.
- Time responsavel.
- Contato principal.
- Onde abrir issues ou tarefas.
- Se existira ambiente de desenvolvimento/execucao compartilhado.
- Se havera CI/CD ou apenas execucao local.
