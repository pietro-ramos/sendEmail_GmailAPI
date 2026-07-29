# Planilhas E PDFs Esperados

Cada planilha representa uma empresa, lista de credores ou mala direta de comunicados. O sistema nao exige um unico nome de cabecalho; ele aceita aliases para permitir listas recebidas em formatos diferentes.

## Leitura De Planilha

A leitura acontece em `util/input_excel.py`.

Por padrao, `pandas.read_excel` le a primeira aba da planilha. Se uma planilha tiver dados em outra aba, cabecalhos deslocados ou blocos de resumo antes da tabela, ela precisa ser normalizada antes do envio ou o carregador precisa ser adaptado.

## Colunas Obrigatorias

O sistema precisa encontrar pelo menos uma coluna de cada grupo.

### Nome

- `Nome do Credor`
- `Nome Credor`
- `Nome`
- `Razao Social/Nome`

### E-mail

- `Email`
- `E-mail`
- `E-MAIL`
- `Email Principal`

### CPF/CNPJ

- `CPF / CNPJ`
- `CPF/CNPJ`
- `CPF`
- `CNPJ/CPF`
- `CNPJ / CPF`

## Colunas Opcionais

Essas colunas sao usadas quando existem, principalmente nos templates.

### Classe

- `Classe`
- `Classe do Credor`

### Valor

- `Valor R$`
- `Valor (R$)`
- `Valor`
- `VALOR`

### Endereco

- `Endereço`
- `Endereco`

### Natureza

- `Natureza`
- `Natureza do Crédito`
- `Natureza/Origem`
- `NATUREZA`

### Origem

- `Origem`
- `Origem do Crédito`
- `Natureza/Origem`
- `ORIGEM`

### Moeda

- `Moeda`
- `Currency`

## Credores Do Exterior

O loader de exterior e ativado por:

```python
USAR_LISTA_EXTERIOR = True
```

Ele usa `carregar_credores_exterior`, aceita `Moeda` e monta o valor como:

```text
{moeda} {valor}
```

Quando `USAR_BUSCA_PDF_EXTERIOR=True`, o envio Outlook usa `GraphEmailServiceExterior`, que procura PDFs pelo nome do credor em vez de CPF/CNPJ.

## Como Os Campos Alimentam O Template

Os templates HTML usam placeholders do Python `str.format`.

Placeholders atualmente suportados:

```text
{nome}
{classe}
{valor}
{cpf_cnpj}
{endereco}
{natureza}
{origem}
```

Se o template usar um placeholder que nao e preenchido pelo servico, o envio daquela mensagem falha na montagem.

## Regra De Nomes Dos PDFs

Os PDFs ficam em:

```text
data/cartas
```

O caminho e definido por `CARTAS_DIR`.

Para credores nacionais, os candidatos sao gerados assim:

```text
<CPF_CNPJ_APENAS_DIGITOS>_<CLASSE_NORMALIZADA>.pdf
<CPF_CNPJ_APENAS_DIGITOS>.pdf
```

Exemplo:

```text
01140047000113_ME_EPP.pdf
01140047000113.pdf
```

Se existir mais de uma carta para o mesmo credor, o sistema tambem procura sufixos numericos:

```text
01140047000113_ME_EPP_2.pdf
01140047000113_ME_EPP_3.pdf
```

## Normalizacao Da Classe

A classe e convertida para ASCII, letras maiusculas e `_` no lugar de caracteres nao alfanumericos.

Exemplos:

```text
ME/EPP -> ME_EPP
Quirografário -> QUIROGRAFARIO
```

Ha compatibilidade especifica para o padrao legado:

```text
QUIROGRAFARIO -> tambem procura QUIROGRAF_RIO
```

## PDFs Do Exterior

Para credores do exterior, a busca pode usar:

```text
<NOME_NORMALIZADO>_<CLASSE_NORMALIZADA>.pdf
<NOME_NORMALIZADO>.pdf
```

Esse modo e usado apenas pela variante `GraphEmailServiceExterior`.

## Validacao Manual Antes Do Envio

Antes de rodar `main.py`, confira:

- a planilha configurada existe;
- a primeira aba contem a tabela esperada;
- as colunas obrigatorias estao presentes;
- os e-mails estao preenchidos;
- o assunto esta correto;
- `CARTAS_DIR` aponta para a pasta correta;
- os PDFs esperados existem quando `ENVIAR_COM_PDF=True`;
- o comunicado nao esta usando uma planilha de teste por engano.
