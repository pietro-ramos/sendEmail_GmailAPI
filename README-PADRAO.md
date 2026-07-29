# Padrão de README — Empresa

Este documento define as seções obrigatórias e opcionais que todo README de projeto da empresa deve conter.

---

## Por que padronizar?

Um README padronizado garante que qualquer pessoa do time consiga:

- Entender o que a aplicação faz em menos de 1 minuto
- Rodar o projeto localmente sem precisar perguntar para ninguém
- Saber onde está rodando e como fazer deploy
- Saber quem procurar quando algo der errado

---

## Seções obrigatórias — todo tipo de aplicação

### 1. Descrição

O que a aplicação faz, em 2–3 linhas. Deve responder:

- Qual problema resolve?
- Quem usa?
- Qual o contexto dentro da empresa?

> Exemplo ruim: "Sistema de documentos."
> Exemplo bom: "API de recebimento de documentos para processos de recuperação judicial. Usada pelo time jurídico para coletar arquivos das empresas devedoras antes dos prazos de audiência."

---

### 2. Stack

Liste linguagem, framework e versões principais. Sem isso não dá para abrir o projeto.

| Tecnologia | Versão |
|---|---|
| Java | 21 |
| Spring Boot | 3.2.5 |
| PostgreSQL | 15 |

---

### 3. Pré-requisitos

O que precisa estar instalado na máquina antes de qualquer coisa.

- Ferramentas (Java 21, Node 20, Docker, etc.)
- Contas ou acessos necessários (banco, serviços externos)
- Variáveis de ambiente obrigatórias antes do primeiro `run`

---

### 4. Como rodar localmente

Comandos do zero até a aplicação funcionando. Ordem importa.

```bash
# 1. Clone
git clone <url>

# 2. Configure variáveis de ambiente
cp .env.example .env
# edite o .env com seus valores

# 3. Instale dependências
<comando de instalação>

# 4. Rode
<comando de start>
```

Se houver dependências externas (banco, cache), incluir como sobir com Docker ou indicar onde configurar.

---

### 5. Variáveis de ambiente

Liste **todas** as variáveis obrigatórias, para que servem, e se têm valor padrão.

| Variável | Obrigatória | Descrição | Exemplo |
|---|---|---|---|
| `DATABASE_URL` | Sim | URL de conexão com o banco | `postgresql://user:pass@localhost:5432/db` |
| `SESSION_SECRET` | Sim | Chave de assinatura de sessão | `minha-chave-secreta` |
| `FEATURE_X_ENABLED` | Não | Liga/desliga feature X | `false` |

O repositório deve ter um `.env.example` com todas as variáveis preenchidas com valores fictícios ou padrão.

---

### 6. Como testar

Comando para rodar os testes. Se não houver testes, declarar explicitamente e o motivo.

```bash
# Testes unitários
<comando>

# Testes de integração (se houver)
<comando>
```

---

### 7. Deploy / Ambientes

| Ambiente | URL | Deploy |
|---|---|---|
| Desenvolvimento | `https://app-dev.exemplo.com` | Automático a cada push em `develop` |
| Produção | `https://app.exemplo.com` | Manual via CI após aprovação |

Descreva brevemente como o deploy acontece: CI/CD, ferramenta usada (GitHub Actions, Render, etc.), e se há etapas manuais.

---

### 8. Dono / Contato

| Campo | Valor |
|---|---|
| Time responsável | Nome do time |
| Contato principal | Nome + canal (Slack, e-mail) |
| Onde abrir issue | Link do repositório ou board |

---

## Seções específicas por tipo de aplicação

### APIs e Backends

**Rotas principais** — liste as rotas mais importantes ou aponte para a documentação:

```
GET  /api/health          → healthcheck
POST /api/auth/login      → autenticação
GET  /api/docs            → Swagger (se disponível)
```

**Dependências externas** — liste os serviços que a aplicação precisa para funcionar:

| Serviço | Finalidade |
|---|---|
| PostgreSQL | Armazenamento principal |
| Redis | Cache de sessões |
| SendGrid | Envio de e-mails |

---

### Frontends

**Backend consumido** — URL do backend por ambiente:

| Ambiente | URL do Backend |
|---|---|
| Local | `http://localhost:8080` |
| Produção | `https://api.exemplo.com` |

**Variáveis de ambiente** — diferenciar públicas de server-side:

- `NEXT_PUBLIC_*` — expostas ao browser, não colocar segredos
- Sem prefixo — server-side only, seguras para segredos

---

### CLIs e Scripts

**Uso** — exemplos reais de como chamar:

```bash
# Exemplo com parâmetros obrigatórios
node script.js --input arquivo.csv --output resultado.json

# Exemplo com flags opcionais
node script.js --input arquivo.csv --dry-run
```

**Saída esperada:**

```
[INFO] Processando 120 registros...
[OK]   Exportado em resultado.json
```

---

## O que não pertence ao README

| Item | Onde fica |
|---|---|
| Histórico de mudanças | `CHANGELOG.md` ou git tags |
| Guia de contribuição detalhado | `CONTRIBUTING.md` |
| Decisões de arquitetura | `docs/ADR-*.md` |
| Runbook de incidentes | Wiki / Notion / Confluence |

---

## Checklist antes de publicar

- [ ] Descrição responde: o que faz, quem usa, qual contexto?
- [ ] Stack com versões listadas
- [ ] Pré-requisitos listados
- [ ] Comandos de `run` testados do zero (em máquina limpa, se possível)
- [ ] `.env.example` existe e está atualizado
- [ ] Todas as variáveis de ambiente documentadas
- [ ] Comando de teste funciona (ou ausência justificada)
- [ ] Ambientes e URLs de deploy corretos
- [ ] Contato/dono preenchido
- [ ] Seções específicas do tipo de app preenchidas
