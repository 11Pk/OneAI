# OneAI — Module Explanations

This document explains how each module in the orchestration pipeline works.
Written for clarity — a 3rd-year engineering student should understand every piece.

---

## Architecture Overview

```
User Prompt
    │
    ▼
┌─────────┐     ┌────────────┐     ┌────────┐     ┌──────────┐     ┌──────────┐
│ Planner │ ──► │ Classifier │ ──► │ Router │ ──► │ Enhancer │ ──► │ Provider │
└─────────┘     └────────────┘     └────────┘     └──────────┘     └──────────┘
    │                                                                    │
    │ (if decomposed: multiple tasks run in parallel)                    │
    │                                                                    ▼
    └──────────────────────── asyncio.gather() ──────────────────► Combine
                                                                           │
                                                                           ▼
                                                                    Final Response
```

---

## 1. Planner (`backend/app/modules/planner.py`)

**Purpose:** Decide if the user's prompt is simple (one task) or complex (multiple subtasks).

**How it works:**
1. Sends the prompt to an LLM (OpenRouter) with instructions
2. LLM returns JSON: `{"needs_decomposition": true/false, "subtasks": [...]}`
3. If decomposition is needed, each subtask is processed independently
4. If not, the whole prompt becomes a single task

**Example:**
- Input: `"What is AI?"` → 1 task (no decomposition)
- Input: `"Write a blog post AND create a Python data script"` → 2 subtasks

**Why LLM-based?** Simple and flexible. No custom ML model needed for v1.

---

## 2. Task Classifier (`backend/app/modules/classifier.py`)

**Purpose:** Label each task with a category so the Router knows which AI to use.

**Categories:**
| Category  | Example                              |
|-----------|--------------------------------------|
| coding    | "Write a sorting algorithm in Python" |
| research  | "Explain how photosynthesis works"    |
| writing   | "Draft an email to my professor"      |
| analysis  | "Compare React vs Vue"                |
| general   | Anything else                         |

**How it works:**
1. Sends the task text to an LLM with category definitions
2. LLM returns JSON: `{"category": "coding"}`
3. Falls back to `"general"` if parsing fails

---

## 3. Router (`backend/app/modules/router.py`)

**Purpose:** Map each category to an AI provider. **No LLM call** — just a dictionary lookup.

**Rules:**
```
Coding    → Groq        (fast, good at code)
Research  → Gemini      (strong at factual info)
Writing   → OpenRouter  (versatile models)
Analysis  → OpenRouter  (good reasoning)
General   → OpenRouter  (default)
```

**Why rule-based?** Predictable, easy to change, no API cost. You can edit `CATEGORY_TO_PROVIDER` in one place.

---

## 4. Prompt Enhancer (`backend/app/modules/enhancer.py`)

**Purpose:** Rewrite the user's prompt to get better AI responses.

**How it works:**
1. Takes the original prompt + its category
2. Asks an LLM to improve clarity and structure
3. Sends the **enhanced** prompt to the target provider (not the original)

**Example:**
- Original: `"fix my code"`
- Enhanced: `"Review the following Python code for bugs, explain each issue found, and provide corrected code with comments explaining the fixes. Category: coding"`

---

## 5. AI Providers (`backend/app/providers/`)

**Purpose:** Adapters that talk to external AI APIs. All inherit from `BaseProvider`.

```
BaseProvider (abstract)
├── OpenRouterProvider  → https://openrouter.ai/api/v1/chat/completions
├── GeminiProvider      → https://generativelanguage.googleapis.com/...
└── GroqProvider        → https://api.groq.com/openai/v1/chat/completions
```

Each provider implements one method:
```python
async def generate(self, prompt: str) -> str
```

**Why adapters?** Adding a new provider (e.g., Anthropic) means creating one new file — nothing else changes.

---

## 6. Orchestrator (`backend/app/modules/orchestrator.py`)

**Purpose:** The main coordinator. Runs the full pipeline.

**Normal mode flow:**
```
1. plan(prompt)           → decomposed?, subtasks[]
2. For EACH subtask (in parallel via asyncio.gather):
   a. classify(task)      → category
   b. route(category)     → provider name
   c. enhance(task, cat)  → better prompt
   d. provider.generate() → AI response
3. combine_responses()    → single final message
4. Save to database
```

**Compare mode flow:**
```
1. Skip planner/classifier/router
2. Send same prompt to ALL 3 providers in parallel
3. Return all responses separately
4. User clicks "Choose Best Response" → Judge module
```

---

## 7. Judge (`backend/app/modules/judge.py`)

**Purpose:** Pick the best response when multiple models answered the same prompt.

**How it works:**
1. Receives original prompt + all model responses
2. Sends everything to a Judge LLM with evaluation criteria
3. Judge returns: winner provider, winning text, and reasoning
4. Result saved to `judge_results` table

**Evaluation criteria:** accuracy, completeness, clarity, relevance.

---

## 8. Parallel Execution

All independent tasks use Python's `asyncio.gather()`:

```python
# Multiple subtasks processed at the same time
results = await asyncio.gather(
    _process_single_task("Explain AI", 0),
    _process_single_task("Write Python code", 1),
)

# Compare mode: all providers called simultaneously
responses = await asyncio.gather(
    openrouter.generate(prompt),
    gemini.generate(prompt),
    groq.generate(prompt),
)
```

This is faster than running tasks one after another.

---

## Database Tables

| Table           | Purpose                                    |
|-----------------|--------------------------------------------|
| users           | User accounts (demo user seeded)           |
| conversations   | Chat sessions                              |
| messages        | User prompts + assistant responses         |
| tasks           | Individual work units from the planner     |
| responses       | Raw AI output for each task                |
| judge_results   | Winner + reasoning from compare mode       |

See `database/schema.sql` for full SQL definitions.

---

## Frontend Components

| Component        | File                          | Purpose                        |
|------------------|-------------------------------|--------------------------------|
| Sidebar          | `components/Sidebar.tsx`      | Conversation history           |
| MessageList      | `components/MessageList.tsx`  | Chat bubbles + task details    |
| ChatInput        | `components/ChatInput.tsx`    | Prompt box + compare toggle    |
| ComparePanel     | `components/ComparePanel.tsx` | Side-by-side model responses   |
| LoadingIndicator | `components/LoadingIndicator.tsx` | Animated waiting dots      |

---

## Extending the Platform

**Add a new AI provider:**
1. Create `backend/app/providers/newprovider.py` extending `BaseProvider`
2. Register it in `backend/app/providers/factory.py`
3. Optionally add routing rules in `router.py`

**Change routing rules:**
Edit the `CATEGORY_TO_PROVIDER` dictionary in `router.py`.

**Add a new task category:**
1. Add to `CATEGORIES` in `classifier.py`
2. Add mapping in `router.py`

**Replace LLM planner with custom logic:**
Swap the body of `plan()` in `planner.py` with your own code.
