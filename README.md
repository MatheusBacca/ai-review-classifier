# AI Review Classifier

Servidor Python para cadastro e consulta de reviews usando **FastAPI**, **Uvicorn**,
**Pydantic**, **SQLModel** e **PostgreSQL**.

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
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/reviews_db
```

As configurações são carregadas por um objeto único `settings` em
`app/config.py`, usando `BaseSettings` e `SettingsConfigDict`.

### Arquivo `.env.axample`

Variáveis atualmente utilizadas pelo projeto:

- `DATABASE_URL`: string de conexão com PostgreSQL usada pelo SQLModel.

## Executando a API

```bash
uvicorn app.main:app --reload
```

Documentação automática:
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

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

## Estrutura de dados

Tabela de reviews:

- `id`: inteiro (chave primária)
- `customer_name`: string
- `review_date`: datetime
- `review_text`: string
- `classification`: enum string (`positive`, `neutral`, `negative`)

## Endpoints

### `POST /reviews`
Cria uma review.

Exemplo de body:

```json
{
  "customer_name": "Maria Souza",
  "review_date": "2026-04-23T14:30:00",
  "review_text": "Atendimento excelente e entrega rápida.",
  "classification": "positive"
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