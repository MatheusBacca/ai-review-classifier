# AI Review Classifier

API REST para cadastro de reviews de clientes, classificacao automatica de sentimento e
consulta analitica com filtros por periodo. O fluxo principal recebe o texto da review,
classifica o sentimento e persiste os dados para consultas e relatorios.

## Overview

### Stack completa

- **Linguagem:** Python 3.11+
- **API/Web:** FastAPI, Starlette, Uvicorn
- **Modelagem/validacao:** Pydantic v2, SQLModel
- **Banco de dados:** PostgreSQL (producao) e SQLite em memoria (testes)
- **ORM/SQL:** SQLAlchemy 2
- **NLP/IA:** Hugging Face Transformers (modelo multilingual sentiment)
- **Testes:** Pytest, FastAPI TestClient, fixtures/mocks com monkeypatch
- **Qualidade de codigo:** Black
- **Config:** pydantic-settings com variaveis em `.env`
- **Observabilidade:** logging estruturado JSON com rotacao de arquivos e request-id

## Requisitos

- Python 3.11+
- PostgreSQL 14+ (ou compatível)

## Instalação

1. Clone o projeto e entre na pasta:

```bash
git clone <url-do-repositorio>
cd ai-review-classifier
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

3. Instale as bibliotecas:

```bash
pip install -r requirements.txt
```

4. Crie o arquivo `.env` com base em `.env.axample`:

```bash
# Windows (PowerShell)
copy .env.axample .env

# Linux/macOS
cp .env.axample .env
```

5. Edite o arquivo `.env` e ajuste as variáveis de ambiente:

```env
# PostgreSQL connection URL used by SQLModel engine.
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/reviews_db

# Optional token da Hugging Face
HUGGINGFACE_TOKEN=hf_...
```

As configurações são carregadas por um objeto único `settings` em
`app/config.py`, usando `BaseSettings` e `SettingsConfigDict`.

### Arquivo `.env.axample`

Variáveis atualmente utilizadas pelo projeto:

- `DATABASE_URL`: string de conexão com PostgreSQL usada pelo SQLModel.
- `HUGGINGFACE_TOKEN`: (opcional) token de acesso ao hugging face hub para melhor experiência com o modelo de análise de sentimento utilizado.
- `LOG_LEVEL`: nivel de log da aplicacao (ex.: `INFO`, `DEBUG`).
- `LOG_DIRECTORY`: pasta onde os arquivos de log serao gravados.
- `LOG_ROTATION_MAX_MB`: tamanho maximo por arquivo de log antes de rotacionar.
- `LOG_BACKUP_COUNT`: quantidade maxima de arquivos rotacionados mantidos (limite de 10).

## Executando a API

```bash
uvicorn app.main:app --reload
```

Documentação automática:
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Logging estruturado

O projeto possui middleware HTTP para logs de entrada e saida de requisicoes, com:

- metodo, endpoint, query params, path params e headers sanitizados;
- body da requisicao (quando aplicavel, com truncamento para payloads grandes);
- status de resposta, duracao da request e metadados de processo/thread;
- correlacao por request-id em todos os logs.

### Idempotency ID / Request ID

- a API aceita os headers `Idempotency-Key`, `X-Idempotency-Key` e `X-Request-Id`;
- se nenhum for enviado, um UUID e gerado automaticamente;
- o id utilizado volta no header de resposta `X-Request-Id`;
- o mesmo id e registrado nos logs para rastreabilidade ponta a ponta.

### Rotacao de arquivos de log

- os logs sao escritos em JSON no arquivo `logs/application.log`;
- a rotacao ocorre ao atingir `LOG_ROTATION_MAX_MB`;
- sao mantidos no maximo `LOG_BACKUP_COUNT` arquivos (ate 10).

## Formatação com Black (PEP8)

```bash
black app
```

## Arquitetura do projeto

Estrutura modular atual:

- `app/main.py`: app factory (`create_app`) e instância `app`
- `app/routes/`: roteadores HTTP (ex.: `reviews.py`)
- `app/database/`: engine, sessões e criação de tabelas
- `app/config/`: configurações e objeto único `settings`
- `app/models/`: modelos SQLModel/Pydantic
- `app/utils/`: utilitários compartilhados (ex.: enums)
- `tests/`: testes unitários com Pytest

## Estrutura de dados

Tabela de reviews:

- `id`: inteiro (chave primária)
- `customer_name`: string
- `review_date`: datetime
- `review_text`: string
- `classification`: string

## Endpoints

### `POST /reviews`
Cria uma review e calcula automaticamente a classificacao de sentimento.
Regras de validacao principais:

- `customer_name` obrigatorio e nao pode conter apenas espacos;
- `review_text` obrigatorio e nao pode ser vazio/nem somente espacos.

Exemplo de body:

```json
{
  "customer_name": "Daiane Babicz",
  "review_date": "2026-04-23T14:30:00",
  "review_text": "Atendimento excelente e entrega rápida."
}
```

### `GET /reviews`
Lista reviews com filtros opcionais de período:

- `start_date` (datetime)
- `end_date` (datetime)

Exemplo:

```bash
GET /reviews?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59
```

### `GET /reviews/{id}`
Retorna uma review por ID com os mesmos filtros opcionais de período:

- `start_date` (datetime)
- `end_date` (datetime)

Exemplo:

```bash
GET /reviews/1?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59
```

### `GET /reviews/report`
Retorna um relatório agregado por classificação no período informado:

- `start_date` (datetime)
- `end_date` (datetime)

Exemplo:

```bash
GET /reviews/report?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59
```

## Testes unitarios com pytest

Os testes foram organizados para validar as principais funcionalidades do servico:

- Inserção de review no banco (SQLite em memoria para nao depender do Postgres local);
- Leitura com filtros de periodo usados nas APIs;
- Relatório agregado por classificação;
- Análise de sentimento do Transformer com pipeline mockado;
- Validacoes reprovadas de API (payload invalido, datas invalidas e recurso nao encontrado).

### Executar testes

Com ambiente virtual ativo:

```bash
pytest -v
```

Opcional (modo detalhado com print/log):

```bash
pytest -vv -s
```

### Como configurar dados ficticios dos testes

Arquivo: `tests/test_data.py`

- Os testes usam `get_seed_reviews()` para copiar ou uma lista default de casos de teste, ou uma lista de casos de teste em um arquivo `tests/test_data.json`, se existir;
- `classification` em cada objeto deve conter o valor esperado para validacao.

Formato esperado do JSON:

```json
[
  {
    "customer_name": "Daiane Babicz",
    "review_date": "2026-04-20T10:00:00",
    "review_text": "Produto excelente e entrega rapida.",
    "classification": "positiva"
  }
]
```

### Como definir casos de teste para o Transformer

Arquivo: `tests/test_transformer.py`

O teste instancia `ReviewClassifier` com um `classifier` fake:

```python
classifier = ReviewClassifier(classifier=lambda _text: [{"label": "5 stars"}])
```

Para criar novos cenarios:

- Altere o `label` retornado (`"1 stars"` ate `"5 stars"`);
- Valide a classificacao esperada (`negativa`, `neutra`, `positiva`);
- Inclua novas asserts para formatos diferentes de texto, se necessario.
- Para cenarios maiores, coloque os exemplos no JSON externo (`tests/test_data.json`) e reaproveite via `get_seed_reviews()`.

### Fixtures adicionadas

Arquivo: `tests/conftest.py`

- `session`: banco SQLite em memoria isolado por teste;
- `client`: `TestClient` com override de dependencia `get_session`;
- `seed_reviews`: carrega dados de `get_seed_reviews()`;
- `fake_classifier`: mock deterministico para o classificador.