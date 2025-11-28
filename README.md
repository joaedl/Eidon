# Eidos - Parametric CAD System MVP

Ett kod-first, AI-ready, parametriskt CAD-system byggt som MVP.

## Översikt

Eidos är ett parametriskt CAD-system där modeller representeras som kod/DSL i backend, kompileras till en intern IR (JSON/AST), och används för att:
- Bygga 3D-geometri via CadQuery/OpenCascade
- Göra enkla tolerans- och måttkedjeanalyser (1D stackups)
- Exponera modellen via API till frontend och LLM-agent

## Projektstruktur

```
Eidos/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Kärnmoduler (IR, DSL parser, builder, analysis)
│   │   └── main.py      # FastAPI entrypoint
│   ├── pyproject.toml   # Python dependencies
│   └── default.dsl      # Exempelmodell
└── frontend/            # React + TypeScript frontend
    ├── src/
    │   ├── components/   # React-komponenter
    │   ├── api/         # API client
    │   └── types/       # TypeScript typer
    └── package.json     # Node dependencies
```

## Installation

### Backend

```bash
cd backend
pip install -e .
```

**Konfiguration:**

Skapa en `.env`-fil i projektets rotkatalog (Eidos/) med din OpenAI API-nyckel:

```bash
# Kopiera exempelfilen
cp .env.example .env

# Redigera .env och lägg till din API-nyckel
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Frontend

```bash
cd frontend
npm install
```

## Körning

### Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend API kommer att köras på `http://localhost:8000`

### Frontend

```bash
cd frontend
npm run dev
```

Frontend kommer att köras på `http://localhost:5173`

## Användning

1. Starta backend och frontend (se ovan)
2. Öppna frontend i webbläsaren
3. Standardmodellen (shaft) laddas automatiskt
4. Du kan:
   - Ändra parametrar i parameterpanelen
   - Redigera DSL-koden i DSL-editorn
   - Skicka kommandon till AI-agenten (stubbad i MVP)

## DSL Syntax

Exempel på DSL:

```dsl
part shaft {
  param dia = 20 mm tolerance g6
  param length = 80 mm

  feature base = cylinder(dia_param=dia, length_param=length)
  feature chamfer_end = chamfer(edge=end, size_param=1 mm)

  chain length_chain {
    terms = [length]
  }
}
```

### Syntax-element:

- `part <name> { ... }` - Definierar en part
- `param <name> = <value> <unit> [tolerance <class>]` - Parameter med värde, enhet och optional tolerans
- `feature <name> = <type>(<args>)` - Geometrisk feature (cylinder, hole, chamfer)
- `chain <name> { terms = [<param1>, <param2>, ...] }` - Måttkedja för analys

## API Endpoints

- `POST /models/from-dsl` - Parse DSL till IR
- `POST /models/rebuild` - Bygg geometri från IR
- `POST /analysis/chains` - Analysera måttkedjor
- `POST /agent/command` - LLM-agent kommando (kräver OpenAI API-nyckel i .env)

## Teknisk Stack

### Backend
- Python 3.11+
- FastAPI
- CadQuery (OpenCascade)
- sympy
- lark (DSL parser)
- Pydantic

### Frontend
- React + TypeScript
- Vite
- three.js (3D rendering)
- Vanilla CSS

## Utveckling

Koden är strukturerad för att vara lätt att bygga vidare på:
- Modulär arkitektur
- Tydliga kommentarer
- IR-baserad design (lätt att utöka)
- Stubbad LLM-integration (lätt att ersätta)

## Begränsningar i MVP

- Endast single-part geometri (inga assemblies)
- Begränsade feature-typer (cylinder, hole, chamfer)
- Enkel toleranslogik (hårdkodad tabell)
- Worst-case analys (inga statistiska metoder)
- LLM-agent är stubbad

## Licens

MIT

