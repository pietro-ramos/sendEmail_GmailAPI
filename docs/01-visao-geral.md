# Visao Geral E Arquitetura

Este projeto automatiza o envio de comunicados juridicos para credores. Ele foi criado para uso operacional direto, mas esta em reorganizacao para ser mantido por uma equipe pequena em um repositorio privado.

## Conceitos

- Comunicado: execucao de uma mala direta para uma empresa/lista de credores especifica.
- Planilha de credores: arquivo `.xlsx` com destinatarios e dados usados no template.
- Credor: registro carregado da planilha e representado por `models.Credor`.
- Carta/PDF: arquivo individual anexado ao e-mail do credor.
- Provedor de envio: integracao usada para enviar o comunicado, hoje `outlook`, `gmail` ou `locaweb`.
- Devolucao (bounce): falha posterior de entrega, capturada para atualizar o relatorio operacional.
- Relatorio operacional: arquivo Excel com resultado do envio e, quando processadas, as devolucoes.

## Fluxo De Informacao

1. O operador escolhe a empresa/lista de credores editando o bloco de configuracao em `main.py`.
2. `main.py` monta um `ComunicadoConfig`.
3. `app/comunicado_runner.py` carrega a planilha com `util.input_excel`.
4. Cada linha vira um objeto `Credor`.
5. O runner escolhe o servico de envio conforme o provedor.
6. O servico preenche o template HTML com os dados do credor.
7. O servico procura PDFs em `CARTAS_DIR`, quando `require_pdf=True`.
8. O payload/mensagem e enviado pelo provedor.
9. O resultado de cada destinatario e salvo no relatorio configurado.
10. Em outro momento, `main_bounces.py` pode capturar devolucoes e atualizar o relatorio.

## Pontos De Entrada

- `main.py`: envio de comunicados.
- `main_bounces.py`: captura e aplicacao de devolucoes.
- `bounce_debug_gmail.py`: apoio para entender devolucoes Gmail sem destinatario claro.
- `log_report.py`: conversao de `email_log.log` para Excel.

## Modulos

### `app/`

Camada de orquestracao.

- `comunicado_config.py`: dataclass com todos os parametros de uma execucao.
- `comunicado_runner.py`: decide qual loader e qual servico de envio usar.

### `models/`

Modelos de dominio.

- `credor.py`: classe `Credor`, contendo nome, classe, valor, e-mail, CPF/CNPJ, endereco, natureza e origem.

### `util/`

Funcoes auxiliares.

- `input_excel.py`: leitura de planilhas, aliases de colunas e geracao de nomes candidatos para PDFs.

### `services/`

Integracoes e operacoes externas.

- `auth.py`: autenticacao Gmail para envio.
- `graph_auth.py`: autenticacao Microsoft Graph via client credentials.
- `send_email.py`: envio Gmail.
- `graph_email.py`: envio Outlook/Microsoft Graph.
- `graph_email_exterior.py`: variante Graph para credores do exterior.
- `locaweb_email.py`: envio Locaweb.
- `relatorio.py`: escrita do relatorio de resultados.
- `bounce_gmail.py`: captura devolucoes Gmail.
- `bounce_outlook.py`: captura devolucoes Outlook.
- `bounce_report.py`: atualizacao do relatorio com devolucoes.

## Provedores

### Outlook/Microsoft Graph

Servico principal para envio corporativo. Usa `GraphAuth` para obter token e envia por:

```text
https://graph.microsoft.com/v1.0/users/{remetente}/sendMail
```

O payload contem `subject`, `body`, `toRecipients` e `attachments`.

### Gmail

Usa OAuth local com `credentials.json` e `token.json`. A mensagem e montada como MIME via `EmailMessage` e enviada como `raw` base64 pela Gmail API.

### Locaweb

Usa token de API em `LOCAWEB_API_TOKEN`. A mensagem e enviada para `LOCAWEB_API_URL` com corpo MIME multipart dentro do payload JSON.

## Estado Da Reorganizacao

Arquivos legados de devolucoes (bounces) foram separados:

- `bounces.py` foi substituido por `main_bounces.py` + `services/bounce_*`.
- `capture_nonbounces.py` foi substituido por `bounce_debug_gmail.py`.

Essa separacao deixa o envio, a captura de devolucoes e a depuracao em pontos de entrada diferentes.
