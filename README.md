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
- `classification`: string

## Endpoints

### `POST /reviews`
Cria uma review.

Exemplo de body:

```json
{
  "customer_name": "Daiane Babicz",
  "review_date": "2026-04-23T14:30:00",
  "review_text": "Atendimento excelente e entrega rápida.",
  "classification": "positiva"
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
- Análise de sentimento do Transformer com pipeline mockado.

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