# OneAI — AI Orchestration Platform v1

An intelligent AI orchestration system that routes user prompts to the best AI model, decomposes complex tasks, and supports multi-model comparison with an LLM judge.

Built to be **simple and beginner-friendly** — every file is readable by a 3rd-year engineering student.

---

## What It Does

1. User enters a prompt in a ChatGPT-like interface
2. **Planner** decides whether to split the prompt into subtasks
3. **Classifier** labels each task (coding, research, writing, analysis, general)
4. **Router** maps categories to AI providers (Groq, Gemini, OpenRouter)
5. **Enhancer** improves the prompt before sending it to the model
6. Tasks run **in parallel** with `asyncio.gather()`
7. Responses are combined and returned to the user

**Bonus — Compare Mode:** Send the same prompt to all 3 models, then let a **Judge LLM** pick the best response.

---

## Tech Stack

| Layer    | Technology                    |
|----------|-------------------------------|
| Frontend | Next.js, TypeScript, Tailwind |
| Backend  | FastAPI, Python 3.12          |
| Database | PostgreSQL 16                 |
| AI APIs  | OpenRouter, Gemini, Groq      |
| Deploy   | Docker Compose                |

---

## Folder Structure

```
OneAI/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # DB connection
│   │   ├── api/
│   │   │   └── routes.py       # HTTP endpoints
│   │   ├── models/
│   │   │   └── db_models.py    # SQLAlchemy tables
│   │   ├── schemas/
│   │   │   └── api.py          # Request/response shapes
│   │   ├── providers/          # AI API adapters
│   │   │   ├── base.py         # Abstract base class
│   │   │   ├── openrouter.py
│   │   │   ├── gemini.py
│   │   │   ├── groq.py
│   │   │   └── factory.py      # Provider lookup
│   │   └── modules/            # Orchestration logic
│   │       ├── planner.py      # Task decomposition
│   │       ├── classifier.py   # Category labeling
│   │       ├── router.py       # Provider mapping
│   │       ├── enhancer.py     # Prompt improvement
│   │       ├── judge.py        # Best response picker
│   │       └── orchestrator.py # Main coordinator
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js React frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Main chat page
│   │   └── globals.css
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── MessageList.tsx
│   │   ├── ChatInput.tsx
│   │   ├── ComparePanel.tsx
│   │   └── LoadingIndicator.tsx
│   └── lib/
│       ├── api.ts              # Backend HTTP client
│       └── types.ts            # TypeScript interfaces
├── database/
│   └── schema.sql              # PostgreSQL tables
├── docs/
│   ├── MODULES.md              # How each module works
│   ├── API_EXAMPLES.md         # curl examples
│   └── MOCKUPS.md              # UI wireframes
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL + backend)
- [Node.js 18+](https://nodejs.org/) (for frontend)
- API keys from [OpenRouter](https://openrouter.ai/), [Google AI Studio](https://aistudio.google.com/), and [Groq](https://console.groq.com/)

### Step 1: Configure Environment

```bash
# Copy the example env file and add your API keys
cp .env.example .env

# Edit .env and set:
#   OPENROUTER_API_KEY=sk-or-...
#   GEMINI_API_KEY=AI...
#   GROQ_API_KEY=gsk_...
```

### Step 2: Start Database + Backend (Docker)

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port `5432` (auto-runs `database/schema.sql`)
- FastAPI backend on port `8000`

Verify: open http://localhost:8000/docs

### Step 3: Start Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

---

## Local Development (Without Docker)

### Backend

```bash
# Start PostgreSQL yourself, then:
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Run the schema manually against your Postgres:
# psql -U oneai -d oneai -f ../database/schema.sql

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable              | Required | Description                          |
|-----------------------|----------|--------------------------------------|
| `DATABASE_URL`        | Yes      | PostgreSQL connection string         |
| `OPENROUTER_API_KEY`  | Yes      | OpenRouter API key                   |
| `GEMINI_API_KEY`      | Yes      | Google Gemini API key                |
| `GROQ_API_KEY`        | Yes      | Groq API key                         |
| `OPENROUTER_MODEL`    | No       | Default: `openai/gpt-4o-mini`        |
| `GEMINI_MODEL`        | No       | Default: `gemini-2.0-flash`          |
| `GROQ_MODEL`          | No       | Default: `llama-3.3-70b-versatile`   |
| `CORS_ORIGINS`        | No       | Default: `http://localhost:3000`     |
| `NEXT_PUBLIC_API_URL` | No       | Default: `http://localhost:8000`     |

---

## API Endpoints

| Method | Endpoint                          | Description                |
|--------|-----------------------------------|----------------------------|
| GET    | `/api/health`                     | Health check               |
| POST   | `/api/chat`                       | Send prompt, get response  |
| POST   | `/api/judge`                      | Pick best compare response |
| GET    | `/api/conversations`              | List all conversations     |
| GET    | `/api/conversations/{id}`         | Get conversation + messages|
| DELETE | `/api/conversations/{id}`         | Delete a conversation      |

See [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) for curl examples.

---

## How Each Module Works

See [docs/MODULES.md](docs/MODULES.md) for detailed explanations of:
- Planner, Classifier, Router, Enhancer, Judge
- Provider adapters
- Parallel execution with asyncio
- Database schema

See [docs/MOCKUPS.md](docs/MOCKUPS.md) for UI wireframes.

---

## Routing Rules

Simple dictionary lookup in `backend/app/modules/router.py`:

```
Coding    → Groq
Research  → Gemini
Writing   → OpenRouter
Analysis  → OpenRouter
General   → OpenRouter
```

Edit `CATEGORY_TO_PROVIDER` to change these mappings.

---

## Database Tables

| Table           | Stores                                    |
|-----------------|-------------------------------------------|
| `users`         | User accounts                             |
| `conversations` | Chat sessions                             |
| `messages`      | User prompts and assistant replies        |
| `tasks`         | Subtasks created by the planner           |
| `responses`     | Raw AI output per task                    |
| `judge_results` | Winner and reasoning from compare mode    |

Schema: [database/schema.sql](database/schema.sql)

---

## Example Usage

**Simple question:**
> "What is machine learning?"
→ Single task → classified as `research` → routed to **Gemini**

**Coding request:**
> "Write a binary search in Python"
→ Single task → classified as `coding` → routed to **Groq**

**Complex request:**
> "Explain blockchain AND write a Python implementation"
→ Planner splits into 2 tasks → run in parallel → combined response

**Compare mode:**
> Toggle "Multi-Model Comparison Mode" → all 3 models respond → click "Choose Best Response" → Judge picks winner

---

## Extending the Platform

**Add a new AI provider:**
1. Create `backend/app/providers/yourprovider.py` extending `BaseProvider`
2. Register in `factory.py`

**Add a new task category:**
1. Add to `CATEGORIES` in `classifier.py`
2. Add mapping in `router.py`

**Swap LLM planner for custom logic:**
Replace the body of `plan()` in `planner.py`.

---

## License

MIT — use freely for learning and projects.
