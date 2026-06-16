# OneAI — UI Mockups

ASCII wireframes showing the main screens. The actual UI uses Tailwind CSS with a white, minimal ChatGPT-like design.

---

## Screen 1: Empty State (New Chat)

```
┌──────────────┬──────────────────────────────────────────────────────┐
│              │  ☰  OneAI                                            │
│  + New Chat  ├──────────────────────────────────────────────────────┤
│              │                                                      │
│  (empty)     │           OneAI Orchestration                        │
│              │                                                      │
│              │   Enter a prompt and the system will intelligently   │
│              │   route it to the best AI model. Enable comparison   │
│              │   mode to see responses from all models side by side.  │
│              │                                                      │
│              │                                                      │
│              ├──────────────────────────────────────────────────────┤
│              │  ☐ Multi-Model Comparison Mode                       │
│              │  ┌────────────────────────────────────────┐  ┌─────┐ │
│              │  │ Send a message...                      │  │Send │ │
│              │  └────────────────────────────────────────┘  └─────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
     SIDEBAR                        MAIN CHAT AREA
   (gray bg)                      (white bg)
```

---

## Screen 2: Normal Chat Response

```
┌──────────────┬──────────────────────────────────────────────────────┐
│              │  ☰  Write a Python function to...                    │
│  + New Chat  ├──────────────────────────────────────────────────────┤
│              │                                                      │
│  ● Write a   │                    ┌─────────────────────────┐       │
│    Python... │                    │ Write a Python function │       │
│              │                    │ to reverse a string     │       │
│  Explain ML  │                    └─────────────────────────┘       │
│              │                                                      │
│              │  def reverse_string(s):                              │
│              │      return s[::-1]                                  │
│              │                                                      │
│              │  This function uses Python slicing...                │
│              │                                                      │
│              ├──────────────────────────────────────────────────────┤
│              │  ☐ Multi-Model Comparison Mode                       │
│              │  ┌────────────────────────────────────────┐  ┌─────┐ │
│              │  │ Send a message...                      │  │Send │ │
│              │  └────────────────────────────────────────┘  └─────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

User messages: dark bubble, right-aligned.
Assistant messages: plain text with markdown, left-aligned.

---

## Screen 3: Decomposed Task (Multiple Subtasks)

```
┌──────────────┬──────────────────────────────────────────────────────┐
│              │                                                      │
│              │  ### Task 1 (research)                               │
│              │  Quantum computing uses qubits that can be in        │
│              │  superposition...                                    │
│              │                                                      │
│              │  ---                                                 │
│              │                                                      │
│              │  ### Task 2 (coding)                                 │
│              │  ```python                                           │
│              │  import numpy as np                                  │
│              │  # Simple qubit simulation...                        │
│              │  ```                                                 │
│              │                                                      │
│              │  ▸ View 2 subtasks                                   │
│              │                                                      │
└──────────────┴──────────────────────────────────────────────────────┘
```

The "View subtasks" dropdown shows routing details (category → provider).

---

## Screen 4: Compare Mode

```
┌──────────────┬──────────────────────────────────────────────────────┐
│              │  Compare mode — review responses from each model:    │
│              │                                                      │
│              │  ┌─ OPENROUTER ──────────────────────────────────┐ │
│              │  │ Renewable energy reduces carbon emissions...    │ │
│              │  └─────────────────────────────────────────────────┘ │
│              │                                                      │
│              │  ┌─ GEMINI ────────────────────────────────────────┐ │
│              │  │ The main benefits include sustainability...     │ │
│              │  └─────────────────────────────────────────────────┘ │
│              │                                                      │
│              │  ┌─ GROQ ──────────────────────────────────────────┐ │
│              │  │ Key advantages: lower costs, job creation...    │ │
│              │  └─────────────────────────────────────────────────┘ │
│              │                                                      │
│              │  ┌─────────────────────────────────────────────────┐ │
│              │  │          Choose Best Response                   │ │
│              │  └─────────────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

Each provider card has a color-coded border:
- OpenRouter: blue
- Gemini: green
- Groq: orange

---

## Screen 5: After Judge Selection

```
┌──────────────┬──────────────────────────────────────────────────────┐
│              │  ┌─ Best Response — gemini ────────── (purple) ────┐ │
│              │  │ The main benefits include sustainability,       │ │
│              │  │ reduced emissions, and long-term cost savings...  │ │
│              │  └─────────────────────────────────────────────────┘ │
│              │                                                      │
│              │  Judge Reasoning                                     │
│              │  This response provides the most comprehensive and   │
│              │  well-structured answer with clear categorization.   │
│              │                                                      │
│              │  ▸ View all 3 responses                              │
└──────────────┴──────────────────────────────────────────────────────┘
```

---

## Screen 6: Mobile Layout

```
┌─────────────────────────────┐
│  ☰  OneAI                   │
├─────────────────────────────┤
│                             │
│     (chat messages)         │
│                             │
├─────────────────────────────┤
│  ☐ Comparison Mode          │
│  ┌─────────────────┐ Send  │
│  │ Message...      │       │
│  └─────────────────┘       │
└─────────────────────────────┘

Sidebar slides in from left when ☰ is tapped.
Overlay dims the main area.
```

---

## Color Palette

| Element            | Color              |
|--------------------|--------------------|
| Background         | White `#FFFFFF`    |
| Sidebar            | Gray-50 `#F9FAFB`  |
| User bubble        | Gray-900 `#111827` |
| Text               | Gray-800 `#1F2937` |
| Borders            | Gray-200 `#E5E7EB` |
| OpenRouter card    | Blue-50 / Blue-400 |
| Gemini card        | Green-50 / Green-400 |
| Groq card          | Orange-50 / Orange-400 |
| Judge winner       | Purple-50 / Purple-400 |
| Send button        | Gray-900           |
| Choose Best button | Purple-600         |
