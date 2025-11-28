# Eidos Backend

Backend för Eidos parametriska CAD-system.

## Installation

```bash
pip install -e .
```

## Körning

```bash
uvicorn app.main:app --reload --port 8000
```

## Tester

```bash
pytest
```

## Struktur

- `app/core/` - Kärnmoduler:
  - `ir.py` - IR-modeller (Pydantic)
  - `dsl_parser.py` - DSL → IR parser
  - `builder.py` - IR → CadQuery → mesh
  - `analysis.py` - Tolerans- och kedjeanalys

- `app/api/` - FastAPI routes:
  - `routes_models.py` - Modellhantering
  - `routes_analysis.py` - Analysendpoints
  - `routes_agent.py` - LLM-agent (stubbad)

- `app/main.py` - FastAPI app entrypoint

