# OneAI — AI Orchestration Platform 

An intelligent AI orchestration system that routes user prompts to the best AI model, decomposes complex tasks, and supports multi-model comparison with an LLM judge.

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
| Backend  | FastAPI                       |
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


### Step 1: Configure Environment

```bash
# Copy the example env file and add your API keys
cp .env.example .env

```

### Step 2: Start Database + Backend (Docker)

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port `5432` (auto-runs `database/schema.sql`)
- FastAPI backend on port `8000`



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


