# SPEC.md - Scrapped

## 1. Visão Geral do Projeto

**Nome:** Scrapped  
**Tipo:** Aplicação Web de Scraping e Inteligência de Decisores Empresariais  
**Funcionalidade Principal:** Sistema de busca bidirecional que relaciona empresas e decisores empresariais com dados de contato, sem uso de APIs pagas.  
**Usuários Alvo:** Profissionais de vendas, recruitment, e negócios que precisam identificar decisores em empresas específicas.

---

## 2. Arquitetura do Sistema

### 2.1 Composição

```
Scrapped/
├── backend/           # API FastAPI
├── frontend/          # Aplicação React
├── scraping/          # Engine de scraping
└── data/              # Dados (SQLite CNPJ)
```

### 2.2 Stack Tecnológico

| Camada | Tecnologia |
|--------|------------|
| Backend | FastAPI + Uvicorn |
| Autenticação | Authlib (OAuth 2.0 Google) + python-jose (JWT) |
| Fila | Celery + Redis |
| ORM | SQLAlchemy |
| Banco Principal | PostgreSQL |
| Banco Local | SQLite (cnpj.db) |
| NLP | spaCy (pt_core_news_lg) + sentence-transformers |
| Scraping | Playwright + httpx + Scrapy + BeautifulSoup4 |
| Frontend | React + Vite + TanStack Query + Axios + shadcn/ui |

---

## 3. Funcionalidades

### 3.1 Autenticação

- **Login Social:** OAuth 2.0 com Google
- **Proteção de Rotas:** JWT em todas as endpoints autenticadas
- **Acesso:** Apenas usuários autorizados pelo admin

### 3.2 Busca

- **Busca Pontual:** Input único (nome empresa, CNPJ, localização ou nome decisor)
- **Busca em Lote:** Upload de CSV com múltiplas entradas
- **Cargo do Decisor:** Usuário define o cargo que qualifica como decisor
- **Busca Bidirecional:** Empresa → Decisor e Decisor → Empresa

### 3.3 Classificação de Intenção

- Identificação automática do tipo de input:
  - **Empresa** (organização)
  - **Pessoa** (nome próprio)
  - **Localização** (cidade/estado)
  - **Contexto Vago** (ex: "eventos Fortaleza")
- Queries vagas são expandidas via Google Search para descobrir empresas do segmento

### 3.4 Scraping em Paralelo

Três fontes consultadas simultaneamente via Celery tasks:
1. **Receita Federal** - Dados cadastrais da empresa
2. **LinkedIn** - Perfis de decisores
3. **Google + Site da Empresa** - Contatos e informações públicas

### 3.5 Lógica de Merge e Deduplicação

- **Normalização de nome:** unidecode + lowercase + remoção de títulos honoríficos
- **Agrupamento por similaridade:** rapidfuzz com threshold de 85%
- **Validação cruzada:** empresa e/ou localização precisam bater entre fontes
- **Prioridade de campo:**
  - Nome → Receita Federal
  - Cargo → LinkedIn
  - Contato → Site/Google
- **Score de confiança:** +1 ponto por fonte que confirma o mesmo decisor (+0.5 para cargo exato)

### 3.6 Resultado

- Lista rankeada por score de confiança (escala 0-3.5)
- Cada resultado contém:
  - Nome
  - Cargo
  - Empresa
  - E-mail
  - Telefone
  - Perfil LinkedIn
  - Fonte(s) que confirmaram

---

## 4. Modelos de Dados

### 4.1 Usuário

```python
class User:
    id: UUID
    email: str
    name: str
    picture: str
    is_active: bool
    is_admin: bool
    created_at: datetime
```

### 4.2 Busca

```python
class Search:
    id: UUID
    user_id: UUID
    query: str
    target_role: str
    status: enum ("pending", "processing", "completed", "failed")
    search_type: enum ("company", "person", "location", "vague")
    results: list[DecisionMaker]
    created_at: datetime
    completed_at: datetime
```

### 4.3 Decisor

```python
class DecisionMaker:
    id: UUID
    search_id: UUID
    name: str
    role: str
    company: str
    email: str | None
    phone: str | None
    linkedin_url: str | None
    sources: list[str]  # ["rf", "linkedin", "google"]
    confidence_score: float  # 0-3.5
    created_at: datetime
```

---

## 5. API Endpoints

### 5.1 Autenticação

| Método | Endpoint | Descrição |
|--------|----------|------------|
| GET | `/auth/login` | Redirect para OAuth Google |
| GET | `/auth/callback` | Callback OAuth |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Dados do usuário atual |

### 5.2 Busca

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/api/search` | Criar busca pontual |
| POST | `/api/search/batch` | Criar busca em lote (CSV) |
| GET | `/api/search/{id}` | Ver status/resultado |
| GET | `/api/search` | Listar histórico de buscas |

### 5.3 Admin

| Método | Endpoint | Descrição |
|--------|----------|------------|
| GET | `/api/admin/users` | Listar usuários |
| POST | `/api/admin/users/{id}/activate` | Ativar usuário |
| POST | `/api/admin/users/{id}/deactivate` | Desativar usuário |

---

## 6. Frontend - Telas

### 6.1 Login
- Botão "Entrar com Google"
- Redirect para OAuth

### 6.2 Dashboard / Busca Pontual
- Input de busca (empresa, CNPJ, localização, nome)
- Input de cargo do decisor
- Botão de busca
- Results com score de confiança

### 6.3 Busca em Lote
- Upload de CSV
- Mapeamento de colunas
- Status de processamento
- Download de resultados

### 6.4 Histórico
- Lista de buscas anteriores
- Filtros por data, status
- Reutilização de buscas

---

## 7. Regras de Desenvolvimento

### 7.1 LinkedIn
- Nunca fazer login programático
- Injetar cookies de sessão (li_at) obtidos manualmente
- Aplicar playwright-stealth
- Delay 3-8 segundos entre ações
- Máximo 150 perfis/dia por conta

### 7.2 Paralelismo
- Cada fonte (RF, LinkedIn, Google+site) como Celery task独立
- API retorna job_id imediatamente
- Frontend faz polling via TanStack Query

### 7.3 Merge
- Normalização de nome obrigatória
- Threshold 85% no rapidfuzz
- Validação cruzada por empresa/localização

### 7.4 Banco
- PostgreSQL para resultados, usuários, histórico
- SQLite local para base CNPJ (não versionar)
- Redis exclusivamente como broker Celery

---

## 8. O Que NÃO Fazer

- ❌ Usar APIs pagas (Apollo, Lusha, Hunter, Proxycurl)
- ❌ Usar Google Maps API paga (usar omkarcloud/google-maps-scraper)
- ❌ Bloquear API durante scraping (sempre via Celery)
- ❌ Fazer login automático no LinkedIn
- ❌ Subir base SQLite da RF para o repositório