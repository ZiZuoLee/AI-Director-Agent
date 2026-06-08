# AI-Director-Agent
Final Course Project of Fudan University Computer Graph A

## Project Layout

```text
AI-Director-Agent/
├── api.py                 # API entry (uvicorn api:app)
├── start_backend.ps1      # Recommended backend startup script
├── backend/
│   ├── agent/             # Parser, rules, planner, LLM
│   ├── generation/        # Prompt gen, image gen, director agent
│   └── system/            # Pipeline orchestration, storyboard merge
├── frontend/              # React + Vite UI
├── docs/                  # PRD / TRD
├── tests/                 # Smoke tests
├── scripts/               # Local demo scripts
├── images/                # Generated output (gitignored)
└── report/                # English LaTeX report
```

## Quick Start

### 1. Environment

Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`.
Copy `zenmux.env.example` to `zenmux.env` and set `ZENMUX_API_KEY`.

### 2. Backend

```powershell
pip install -r requirements.txt
.\start_backend.ps1
```

Manual start (equivalent):

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

### 3. Frontend (development)

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to port `8000`.

### 4. Production UI

```powershell
cd frontend
npm run build
.\start_backend.ps1
```

FastAPI serves `frontend/dist/` when present.

## API Endpoints

- `GET /api/health`
- `POST /api/plan`
- `POST /api/generate` (`mode`: `simple` or `agentic`)
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/events` (SSE)
- `GET /api/images/{task_id}/{filename}`

## Development Scripts

```powershell
# Agent planning demo
python scripts/agent_demo.py

# ZenMux smoke test
python tests/test_zenmux_api.py

# Director agent smoke test
python tests/test_director_agent.py
```

## Git Workflow

Create feature branches from `pre`, open PRs into `pre`, merge `pre` into `main` when stable.

```bash
git checkout -b feature/your-feature
git push -u origin feature/your-feature
```
