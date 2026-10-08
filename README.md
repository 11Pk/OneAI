# OneAI

OneAI is an AI orchestration app. It decides whether a prompt can go directly to a model or should first be split into smaller tasks. It can then choose a model for each task, run independent tasks at the same time, and show the results in one chat interface.

The design goal is to avoid an LLM call just to decide whether a prompt needs splitting. A small local classifier makes that quick decision; an LLM is used for the more involved work of creating a task plan.

## Problem OneAI Solves

People use AI for different kinds of work, but models have different strengths. Simple prompts should not need a costly planning step, while requests with several actions can be hard to handle as one task. OneAI aims to choose a fitting workflow and model for each request, and to run independent parts in parallel.

## How It Works

```text
                         ┌──────────────────┐
                         │    User Prompt   │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Decomposition Classifier│
                    │       (Local ML)         │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                   NO                        YES
                    │                         │
                    ▼                         ▼
          ┌─────────────────┐      ┌────────────────────┐
          │   Single Task   │      │    LLM Planner     │
          │                 │      │                    │
          │ Direct routing  │      │ Creates subtasks &  │
          │ to a model      │      │ dependencies        │
          └────────┬────────┘      └──────────┬─────────┘
                   │                          │
                   │                          ▼
                   │                ┌────────────────────┐
                   │                │  Task Dependency   │
                   │                │       Graph        │
                   │                └──────────┬─────────┘
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Model Routing       │
                    │                          │
                    │ Task Embedding + FAISS   │
                    │ → Match Model Capability │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Async Execution       │
                    │       asyncio             │
                    │                          │
                    │ Independent tasks run    │
                    │ concurrently             │
                    └────────────┬─────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────┐
              │          Provider Adapters            │
              │                                      │
              │   OpenRouter  │  Gemini  │  Groq     │
              └──────────────────┬───────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Final Response      │
                    │                          │
                    │ Results aggregated and   │
                    │ returned to the frontend │
                    └──────────────────────────┘

```
1. **Decide whether to split.** A local binary classifier predicts whether the prompt has multiple tasks that benefit from a plan. A simple question stays on the direct path.
2. **Build a task graph when needed.** For prompts that need decomposition, an LLM creates subtasks and their dependencies. Tasks without dependencies can run concurrently; dependent tasks wait for their inputs.
3. **Choose a model for each task.** OneAI embeds the task and searches model capability descriptions in a FAISS index. The closest matching model profile is selected from the registry.
4. **Call providers and return results.** Provider adapters handle calls to OpenRouter, Gemini, and Groq. The orchestrator runs eligible work concurrently and returns the responses.

## Decomposition Classifier

The classifier answers one narrow question: **does this prompt need multiple subtasks?** It does not decide which model will answer the prompt.

### Training data

There was no ready-made dataset labeled specifically for decomposition. The project uses annotated Alpaca prompts and combines annotation signals and prompt patterns into a decomposition score. The highest-scoring prompts are labeled `1` (decomposition needed); the lowest-scoring are labeled `0` (not needed). The resulting dataset has 6,000 rows, balanced at 3,000 per label. Training uses an 80/20 stratified split.

### Text features

The training experiments compare three ways to represent a prompt:

- **TF-IDF** captures words and short phrases, such as “compare” or “write a report.”
- **Sentence embeddings** capture meaning, so differently worded prompts with similar intent can have related representations.
- **Hybrid features** combine both. The TF-IDF vector is reduced with TruncatedSVD before it is combined with the sentence embedding.

### Classifier experiments

The training script evaluates eight configurations using Logistic Regression, Linear SVM, and XGBoost across TF-IDF, embedding, and hybrid features. Logistic Regression is a fast, simple baseline; Linear SVM tests a strong linear boundary for text; XGBoost tests whether nonlinear feature combinations help.

The script reports accuracy, precision, recall, F1, and a confusion matrix. F1 is useful because both kinds of mistakes matter: missing a prompt that needs decomposition and unnecessarily decomposing a simple prompt. Runtime currently loads the hybrid Logistic Regression model.

## Model Routing and Parallel Work

The model registry describes available models and their capabilities. The project embeds those descriptions, stores their vectors in FAISS, and embeds each task at request time. FAISS returns similar capability descriptions; this is a lightweight semantic search, not a guarantee that a model will produce the best answer.

After planning, the orchestrator uses Python `asyncio` to run independent model calls concurrently. This helps reduce waiting when tasks are I/O-bound API requests. Tasks with dependencies run after the tasks they rely on have completed.

## Other Features

- **Compare mode:** sends a prompt to configured providers in parallel so their answers can be reviewed side by side.
- **Judge:** can evaluate comparison answers and select one with a short rationale. A judge model can still be wrong; its choice is guidance, not verification.
- **Conversation history:** PostgreSQL stores conversations and messages.

## Backend and Frontend

The **backend** is a Python FastAPI service. It exposes chat, comparison/judging, conversation-history, and health endpoints; coordinates planning and routing; calls provider APIs; and connects to PostgreSQL.

The **frontend** is a Next.js and TypeScript chat app. It provides the message view, prompt input, conversation sidebar, and model comparison interface, and sends requests to the backend.

## Technology

| Area           | Tools                                        |
| -------------- | -------------------------------------------- |
| Frontend       | Next.js, React, TypeScript, Tailwind CSS     |
| Backend        | Python, FastAPI                              |
| Planner ML     | scikit-learn, sentence-transformers, XGBoost |
| Model search   | FAISS                                        |
| Database       | PostgreSQL 16                                |
| Providers      | OpenRouter, Gemini, Groq                     |
| Local services | Docker Compose                               |

## Run Locally

You need Docker Compose, Node.js/npm, and API keys for the providers you want to use.

1. Create the root environment file and add your provider keys:

   ```powershell
   Copy-Item .env.example .env
   ```

   Set `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, and `GROQ_API_KEY` in `.env`.

2. Start PostgreSQL and the backend:

   ```powershell
   docker compose up --build
   ```

   PostgreSQL is exposed on port `5432`; the API is at `http://localhost:8000`. On first database creation, Compose loads `database/schema.sql`.

3. In another terminal, configure and start the frontend:

   ```powershell
   cd frontend
   Copy-Item .env.local.example .env.local
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`.

The planner also needs the trained artifacts under `models/hybrid/`. The model router uses the checked-in FAISS index and model registry under `models/`.

## API and Project Files

- Planner training script: `ml/planner1.py`
- Planner dataset: `datasets/planner_dataset/prompt_decomposition_dataset_6000.csv`
- PostgreSQL schema: `database/schema.sql`

## Current Limitations

The decomposition labels are generated from heuristics and should not be treated as ground truth. Similarity scores from model search are not probabilities of answer quality. Provider availability, rate limits, and model capabilities can also affect results.


