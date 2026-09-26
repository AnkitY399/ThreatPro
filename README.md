# ThreatPro

ThreatPro is an intelligent platform combining **geospatial intelligence**, **graph-based analysis**, **audio stream processing**, and **computer vision** for advanced threat detection and situational awareness.

## Tech Stack

- **Frontend**: Next.js 13 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLite
- **Core Modules**:
  - `audio_stream.py` — Real-time audio capture and processing
  - `classifier.py` — Machine-learning-based threat classification
  - `cv_model.py` — Computer vision model inference
  - `graph_builder.py` — Knowledge graph construction and traversal
- **Storage**: SQLite (`ThreatPro.db`)

## Project Structure

```
ThreatPro/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── audio_stream.py
│   │   │   ├── classifier.py
│   │   │   ├── cv_model.py
│   │   │   └── graph_builder.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── routers/
│   │   │   ├── geospatial.py
│   │   │   ├── graph_intel.py
│   │   │   ├── interceptor.py
│   │   │   └── sentinel.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── dashboard/page.tsx
│   │   └── currency/page.tsx
│   ├── package.json
│   └── tailwind.config.js
├── start_demo.sh
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm / yarn

### 1. Clone the repository

```bash
cd ThreatPro
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to see the application.

## Available Scripts

- `npm run dev` — Start the Next.js dev server
- `npm run build` — Build the frontend for production
- `uvicorn app.main:app --reload` — Run the FastAPI backend

```bash
bash start_demo.sh
```

## License

MIT
