# Desenvolvimento Em Equipe

Este projeto esta migrando de um fluxo individual para manutencao por equipe. A prioridade e separar codigo, configuracao, dados operacionais e segredos.

## Principios

- Codigo deve ser versionado.
- Dados reais de credores nao devem ser versionados.
- Segredos nunca devem entrar no Git.
- Cada comunicado deve ser reproduzivel por configuracao clara.
- Mudancas de regra de negocio devem ser documentadas.
- Alteracoes em templates devem ser revisadas como mudancas funcionais.

## Convencoes De Nomenclatura

### Dominio

Use estes termos na documentacao, PRs e novas configuracoes:

- Comunicado: execucao operacional de uma mala direta para uma empresa/lista de credores.
- Mala direta: envio em massa de comunicados individualizados.
- Lista de credores: planilha de entrada com destinatarios e dados do template.
- Carta/PDF: documento individual anexado ao e-mail do credor.
- Devolucao (bounce): falha posterior de entrega.
- Relatorio operacional: arquivo Excel com resultado do envio e devolucoes processadas.

Evite termos de marketing como campanha, lead, prospect, newsletter ou disparo promocional.

### Python

- Modulos e arquivos: `snake_case.py`.
- Funcoes: `snake_case`.
- Classes: `PascalCase`.
- Constantes: `UPPER_SNAKE_CASE`.

### Comunicados E Arquivos Locais

Para arquivos locais fora do Git, prefira nomes descritivos:

```text
data/<empresa>_lista_cartas.xlsx
data/<empresa>_relatorio_envio.xlsx
data/cartas/<cpf_cnpj>_<classe>.pdf
```

Evite misturar arquivos finais e testes sem marcador claro:

```text
edumax_lista_cartas_teste.xlsx
edumax_lista_cartas_final.xlsx
```

## Fluxo De Trabalho Recomendado

1. Criar branch por tarefa.
2. Fazer alteracoes pequenas e revisaveis.
3. Nao commitar arquivos em `data/`.
4. Rodar validacao sintatica antes do PR.
5. Descrever no PR se a mudanca afeta envio, planilha, payload, devolucoes ou relatorio.
6. Pedir revisao quando alterar templates, nomes de PDFs ou regras de planilha.

Validacao sintatica:

```powershell
.\.venv\Scripts\python.exe -m compileall app models services util main.py main_bounces.py log_report.py bounce_debug_gmail.py
```

## Areas Sensíveis

### `config.py`

Concentra defaults e templates. Hoje ainda mistura configuracao global, parametros do comunicado e corpo HTML. Mudancas aqui podem alterar envios reais.

### `main.py`

Define qual comunicado sera executado. Antes de rodar, revisar o bloco de configuracao.

### `util/input_excel.py`

Contem a regra de negocio de leitura de planilhas e nomes de PDFs. Qualquer alteracao pode afetar todos os comunicados.

### Servicos De Envio

- `services/graph_email.py`
- `services/send_email.py`
- `services/locaweb_email.py`

Alteracoes nesses arquivos podem mudar payload, anexos, retries, limites e logs.

## Melhorias Recomendadas

### Configuracoes Por Comunicado

Criar um diretorio `configs/` com arquivos por empresa:

```text
configs/
  edumax.yaml
  fastsystem.yaml
  ferrari.yaml
```

Cada arquivo poderia declarar:

```yaml
provider: outlook
arquivo_emails: data/edumax_lista_cartas.xlsx
cartas_dir: data/cartas
require_pdf: true
lista_exterior: false
assunto: "AVISO AOS CREDORES - ..."
template: templates/edumax.html
```

### Templates Separados

Mover HTML de `config.py` para:

```text
templates/
  scz_pdf.html
  rdv_gmail.html
  ferrovelho.html
```

Isso reduz risco de conflito e facilita revisao.

### Validacao De Comunicado

Adicionar um comando de dry run para:

- validar colunas obrigatorias;
- contar credores;
- listar e-mails vazios;
- conferir PDFs ausentes;
- mostrar amostra de payload sem enviar.

### Testes Automatizados

Priorizar testes para:

- aliases de colunas;
- normalizacao de CPF/CNPJ;
- normalizacao de classe;
- nomes candidatos de PDFs;
- formatacao de valor;
- montagem de payload Graph;
- atualizacao de devolucoes no relatorio.

## Antes De Abrir O Repositorio Privado

- Garantir que `.gitignore` cobre dados reais e segredos.
- Remover segredos hardcoded de `config.py`.
- Verificar historico Git se algum segredo ja foi commitado.
- Criar planilhas-modelo anonimizadas.
- Criar README com fluxo de instalacao e execucao.
- Documentar permissões exigidas no Azure/Google/Locaweb.
- Definir responsaveis por liberar remetentes e credenciais.
