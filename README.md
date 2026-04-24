# Gestao de Candidatos AP

Aplicacao web para gerenciar candidatos aprovados, substituindo a planilha Google atual e integrando com o **Converts**.

- Backend: **Python 3.11 + Flask 3 + SQLAlchemy + Flask-Login + Flask-Migrate + APScheduler**
- Banco: **PostgreSQL** (SQLite no dev se quiser)
- Frontend: templates Jinja + CSS proprio
- Deploy: **Render** (web service + Postgres)

## Recursos

- Login com perfis Administrador / Operacional
- Tela 1: **Controle de Candidatos AP** com 26 colunas (A..Z), filtros, exportacao Excel
- Tela 2: **Funil de Contratacao** (linhas Data de Inicio e Data de D+1) com calculo de perda automatico
- Tela de **Relatorios** (totais e perdas por etapa, loja, funcao)
- Tela de **Logs de Sincronizacao**
- **Sincronizacao diaria automatica** com o Converts (APScheduler)
- Botao manual **"Sincronizar Converts agora"** (apenas admin)
- Deduplicacao por nome + data da entrevista + vaga
- Gestao de usuarios e lojas (admin)

## Estrutura

```
wsgi.py
config.py
requirements.txt
Procfile
render.yaml
runtime.txt
.env.example
app/
  __init__.py             # Application factory
  extensions.py           # db, login_manager, migrate, csrf
  models.py               # User, Store, Candidate, FunnelRecord, SyncLog, ListOption
  cli.py                  # flask seed | sync-converts | create-user
  constants.py            # Listas (entrevistadores, etapas, etc)
  scheduler.py            # APScheduler diario
  blueprints/
    main.py | auth.py | candidates.py | funnel.py
    reports.py | sync.py | admin.py
  converts/
    client.py             # ConvertsClient (login, get_candidates_by_date, get_stores)
    normalizer.py         # mapeia payload Converts -> Candidate
    sync_service.py       # orquestra a sincronizacao
  templates/
    base.html
    auth/login.html
    candidates/list.html, form.html
    funnel/list.html, form.html
    reports/index.html
    sync/logs.html
    admin/users.html, user_form.html, stores.html
  static/
    css/app.css | js/app.js
migrations/
  alembic.ini, env.py, script.py.mako, versions/0001_initial.py
```

## Variaveis de ambiente

Copie `.env.example` para `.env` e ajuste:

| Variavel | Descricao |
|---|---|
| `SECRET_KEY` | Chave secreta do Flask |
| `DATABASE_URL` | URL do Postgres (Render fornece pronta) |
| `CONVERTS_BASE_URL` | URL base da API do Converts |
| `CONVERTS_LOGIN` | Login do Converts |
| `CONVERTS_SENHA` | Senha do Converts |
| `ADMIN_EMAIL` | E-mail do admin inicial |
| `ADMIN_PASSWORD` | Senha do admin inicial |
| `ADMIN_NAME` | Nome do admin inicial |
| `ENABLE_SCHEDULER` | true/false (default true) |
| `SYNC_HOUR`/`SYNC_MINUTE` | Horario do job diario |
| `TZ` | Timezone (default America/Sao_Paulo) |

## Rodando local (Windows / Linux / Mac)

Pre-requisitos: Python 3.11+, PostgreSQL local **ou** SQLite (default fallback).

```bash
git clone https://github.com/ericasuzana852-sudo/gestao-candidatos-ap.git
cd gestao-candidatos-ap
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # edite os valores
export FLASK_APP=wsgi.py            # Windows: set FLASK_APP=wsgi.py
flask db upgrade                   # cria as tabelas
flask seed                         # cria o admin inicial
flask run --port 5000
```

Acesse http://localhost:5000 e faca login com o e-mail/senha definidos em `.env`.

## Comandos uteis

```bash
flask seed                                # cria/garante o admin inicial
flask sync-converts                       # roda a sincronizacao agora (CLI)
flask create-user --email a@b.com --password 123 --name "Fulana" --role operacional
flask db migrate -m "mensagem"            # gera nova migration
flask db upgrade                          # aplica migrations
```

## Deploy no Render (Blueprint)

1. Faca **fork** ou push deste repositorio na sua conta GitHub.
2. No Render: **New > Blueprint** e aponte para o repositorio. O `render.yaml` ja descreve o web service + banco Postgres + variaveis.
3. Preencha as variaveis marcadas como `sync: false`:
   - `CONVERTS_LOGIN`
   - `CONVERTS_SENHA`
   - `ADMIN_PASSWORD`
4. O `preDeployCommand` (`flask db upgrade && flask seed`) ja cria as tabelas e o admin inicial automaticamente.
5. O servico inicia com Gunicorn em `wsgi:app`.

### Render Cron Job (opcional, recomendado)

No plano free do Render o web service hiberna quando ocioso, entao o APScheduler interno pode nao disparar. Crie um **Cron Job** no Render:

- Command: `flask sync-converts`
- Schedule: `30 23 * * *` (todo dia 23:30)
- Use as mesmas variaveis de ambiente do web service

## Integracao Converts - ajustes necessarios

A estrutura de `app/converts/client.py` esta pronta, mas os **endpoints** e o **formato do payload** do Converts precisam ser confirmados. Procure pelos comentarios `AJUSTE` / `TODO`:

1. `login()` - confirmar URL e nome do campo do token
2. `get_candidates_by_date()` - confirmar endpoint e parametros de filtro de data
3. `get_stores()` - confirmar endpoint para a lista de lojas (RELATORIOS)
4. `normalizer.normalize_candidate()` - mapear nomes reais dos campos retornados

Mapeamento esperado (Converts -> tela Controle de Candidatos AP):

| Converts                  | Coluna | Campo no banco        |
|---------------------------|--------|-----------------------|
| Nome do candidato         | D      | `name`               |
| Vaga                      | H      | `role_position`      |
| Proxima entrevista        | A      | `interview_date`     |
| Visto por                 | F      | `screened_by`        |
| Loja (RELATORIOS)         | G      | `store` + tabela `stores` |

## Perfis

- **Administrador**: gerencia usuarios e lojas, executa sincronizacao manual, edita/exclui candidatos, ve relatorios e logs.
- **Operacional**: visualiza/cadastra/edita candidatos, ve funil e relatorios. Nao pode excluir nem disparar sync.

## Proximos passos para validar o Converts real

1. Confirmar o(s) endpoint(s) reais do Converts e ajustar `client.py`.
2. Rodar `flask sync-converts` em ambiente de homologacao com credenciais reais.
3. Inspecionar a tela **Sincronizacao** (`/sync/logs`) para validar contagens e erros.
4. Ajustar `normalizer.py` conforme o JSON real (renomear keys se necessario).
5. Confirmar timezone do scheduler e ajustar `SYNC_HOUR`/`SYNC_MINUTE`.

## Licenca

Uso interno.
