# [Nome da Aplicação]

> [Descrição em 2–3 linhas: o que faz, quem usa, qual problema resolve.]

---

## Stack

| Tecnologia | Versão |
|---|---|
| | |
| | |
| | |

---

## Pré-requisitos

- [ ] 
- [ ] 
- [ ] 

---

## Como rodar localmente

```bash
# 1. Clone
git clone <url>
cd <pasta>

# 2. Configure variáveis de ambiente
cp .env.example .env
# edite o .env com seus valores

# 3. Instale dependências


# 4. Rode

```

---

## Variáveis de ambiente

Copie `.env.example` e preencha os valores. Todas as variáveis obrigatórias estão listadas abaixo.

| Variável | Obrigatória | Descrição | Exemplo |
|---|---|---|---|
| | Sim | | |
| | Sim | | |
| | Não | | |

---

## Como testar

```bash
# Testes unitários


# Testes de integração (se houver)

```

> Se não houver testes: descreva o motivo aqui.

---

## Deploy / Ambientes

| Ambiente | URL | Como fazer deploy |
|---|---|---|
| Desenvolvimento | | |
| Produção | | |

---

## Dono / Contato

| Campo | Valor |
|---|---|
| Time responsável | |
| Contato principal | |
| Onde abrir issue | |

---

<!-- APAGUE AS SEÇÕES QUE NÃO SE APLICAM AO SEU TIPO DE APP -->

## Rotas principais *(APIs e Backends)*

```
GET  /         → 
POST /         → 
```

> Documentação completa: [link para Swagger / Postman / wiki]

### Dependências externas

| Serviço | Finalidade |
|---|---|
| | |
| | |

---

## Backend consumido *(Frontends)*

| Ambiente | URL do Backend |
|---|---|
| Local | `http://localhost:8080` |
| Produção | |

**Variáveis públicas vs. server-side:**
- `NEXT_PUBLIC_*` — expostas ao browser, não colocar segredos
- Sem prefixo — server-side only

---

## Uso *(CLIs e Scripts)*

```bash
# Uso básico


# Com opções

```

**Saída esperada:**
```

```
