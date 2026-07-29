# Devolucoes (Bounces), Logs E Relatorios

O sistema separa envio e tratamento de devolucoes. O envio inicial gera um relatorio de status imediato. A captura de devolucoes (bounces) pode ser executada depois para marcar falhas que aparecem apos a tentativa de entrega.

## Relatorio De Envio

Ao final de `main.py`, `Relatorio().gerar_relatorio(logs_envio)` salva o resultado em:

```python
ARQUIVO_RELATORIO
```

As colunas principais sao:

- `Destinatario`
- `Status do envio`
- `Erro`

Observacao: o nome `ARQUIVO_RELATORIO` hoje tambem e usado no fluxo de devolucoes. Na pratica, ele representa o relatorio operacional do comunicado.

## Log De Auditoria

Os servicos registram eventos em:

```text
email_log.log
```

Esse arquivo contem status, erros de envio, erros de montagem de payload e informacoes de PDFs encontrados ou ausentes.

Logs nao devem ser versionados.

## Gerar Excel A Partir Do Log

Execute:

```powershell
.\.venv\Scripts\python.exe log_report.py
```

Saida:

```text
email_log.xlsx
```

Abas possiveis:

- `envios`: registros de envio identificados no log.
- `erros`: mensagens de erro extraidas do log.

## Processar Devolucoes

Configure o provedor em `config.py` ou por variavel de ambiente:

```text
BOUNCE_PROVIDER_DEFAULT=outlook
```

Execute:

```powershell
.\.venv\Scripts\python.exe main_bounces.py
```

Fluxo:

1. `main_bounces.py` escolhe `buscar_bounces_outlook` ou `buscar_bounces_gmail`.
2. O servico busca mensagens de devolucao.
3. Extrai destinatario e motivo.
4. `services.bounce_report` abre `ARQUIVO_RELATORIO`.
5. Normaliza os e-mails.
6. Atualiza `Status do envio`, `Motivo do bounce` e `Erro`, quando existir.

## Devolucoes Outlook

Arquivo:

```text
services/bounce_outlook.py
```

Usa Microsoft Graph para buscar mensagens na caixa do remetente configurado. Os filtros consideram:

- assunto configurado em `ASSUNTO_NDR_OUTLOOK`;
- mensagens com termos como falha na entrega;
- data de corte `BOUNCE_AFTER_DATE_OUTLOOK`;
- limites `BOUNCE_MAX_MESSAGES` e `BOUNCE_PAGE_SIZE`.

## Devolucoes Gmail

Arquivo:

```text
services/bounce_gmail.py
```

Usa Gmail readonly. A query inclui assuntos de delivery status e a data:

```text
BOUNCE_AFTER_DATE_GMAIL
```

Quando o destinatario nao e identificado, o ID da mensagem e salvo em:

```text
emails_sem_destinatario.txt
```

## Depurar Devolucoes Gmail Sem Destinatario

Execute:

```powershell
.\.venv\Scripts\python.exe bounce_debug_gmail.py
```

Ele le `emails_sem_destinatario.txt` e grava corpos em:

```text
corpos_emails_para_analise.txt
```

Use esse arquivo apenas localmente, pois pode conter dados sensiveis.

## Cuidados

- Processar devolucoes somente depois de confirmar que `ARQUIVO_RELATORIO` aponta para o relatorio do comunicado correto.
- Salvar uma copia do relatorio antes de atualizar devolucoes.
- Revisar o assunto usado para busca, principalmente no Outlook.
- Nao versionar logs, relatorios reais ou corpos de e-mail.
