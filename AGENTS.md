# Project: Enterprise Narrative Analyst

## Stack
- Python 3.12, FastAPI, SQLAlchemy 2 (async), pgvector on Postgres 16
- Docker Compose for local infra
- OpenAI for embeddings (text-embedding-3-small) and generation (gpt-4o-mini)

## Before you write code
- Read `v1-implementation-plan.md` for architecture decisions and rationale
- All new services must implement the Protocol interfaces in `app/embeddings/base.py`
  and `app/generation/base.py` — never call OpenAI directly from business logic
- Always write test cases first, create a new file in `tests/` directory. 
    - Follow the same naming and folder structure as the code you are testing.
    - Run `pytest tests/ -v` to test the test suite
    - Fix code until all tests pass

## Running the stack
docker compose up -d
python -m app.ingestion.ingest --help

## Running tests
pytest tests/ -v

## Code conventions
- All DB access must go through the async session in `app/db.py`
- Never use sync SQLAlchemy calls
- Pydantic models for all API inputs and outputs — no raw dicts at boundaries
- Chunk metadata (company, doc_type, fiscal_period) must always be denormalized
  onto the chunks table — do not join to documents at query time

## Do not modify
- migrations/ — schema changes need a new numbered file, not edits to existing ones
- The EmbeddingProvider and GenerationProvider protocols