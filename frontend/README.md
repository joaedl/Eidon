# Eidos Frontend

Frontend för Eidos parametriska CAD-system.

## Installation

```bash
npm install
```

## Körning

```bash
npm run dev
```

Frontend körs på `http://localhost:5173` och förväntar sig backend på `http://localhost:8000`.

## Bygga för produktion

```bash
npm run build
```

## Struktur

- `src/components/` - React-komponenter:
  - `Viewer3D.tsx` - Three.js 3D-viewer
  - `ParameterPanel.tsx` - Parameterredigering
  - `DSLCodeEditor.tsx` - DSL-kodredigerare
  - `PromptPanel.tsx` - AI-agent prompt-panel

- `src/api/` - API-klient för backend-kommunikation

- `src/types/` - TypeScript-typer som speglar backend-IR

- `src/App.tsx` - Huvudapplikationskomponent

