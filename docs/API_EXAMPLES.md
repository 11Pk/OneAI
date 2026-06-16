# OneAI Orchestration Platform — API Examples

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## 1. Health Check

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "OneAI Orchestration Platform"
}
```

---

## 2. Send a Chat Message (Normal Mode)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to reverse a string",
    "conversation_id": null,
    "compare_mode": false
  }'
```

**Response:**
```json
{
  "conversation_id": "uuid-here",
  "message_id": "uuid-here",
  "user_message": "Write a Python function to reverse a string",
  "assistant_message": "def reverse_string(s):\n    return s[::-1]",
  "compare_mode": false,
  "compare_responses": null,
  "tasks": [
    {
      "task_index": 0,
      "category": "coding",
      "provider": "groq",
      "original_prompt": "Write a Python function to reverse a string",
      "enhanced_prompt": "Write a clean Python function...",
      "response": "def reverse_string(s):\n    return s[::-1]"
    }
  ],
  "decomposed": false
}
```

---

## 3. Send a Complex Prompt (Decomposition)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing and write a Python script to simulate a qubit",
    "conversation_id": null,
    "compare_mode": false
  }'
```

The planner will split this into 2 subtasks:
1. "Explain quantum computing" → Research → Gemini
2. "Write Python script for qubit simulation" → Coding → Groq

Both run in **parallel** via `asyncio.gather()`.

---

## 4. Multi-Model Comparison Mode

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the benefits of renewable energy?",
    "conversation_id": null,
    "compare_mode": true
  }'
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": "What are the benefits of renewable energy?",
  "assistant_message": "Compare mode: review responses below...",
  "compare_mode": true,
  "compare_responses": [
    { "provider": "openrouter", "model": "openai/gpt-4o-mini", "content": "..." },
    { "provider": "gemini", "model": "gemini-2.0-flash", "content": "..." },
    { "provider": "groq", "model": "llama-3.3-70b-versatile", "content": "..." }
  ],
  "tasks": null,
  "decomposed": false
}
```

---

## 5. Judge — Choose Best Response

After compare mode, call the judge:

```bash
curl -X POST http://localhost:8000/api/judge \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "assistant-message-uuid",
    "original_prompt": "What are the benefits of renewable energy?",
    "responses": [
      { "provider": "openrouter", "model": "openai/gpt-4o-mini", "content": "Response A..." },
      { "provider": "gemini", "model": "gemini-2.0-flash", "content": "Response B..." },
      { "provider": "groq", "model": "llama-3.3-70b-versatile", "content": "Response C..." }
    ]
  }'
```

**Response:**
```json
{
  "selected_provider": "gemini",
  "selected_response": "Response B...",
  "reasoning": "This response provides the most comprehensive and well-structured answer..."
}
```

---

## 6. List Conversations

```bash
curl http://localhost:8000/api/conversations
```

---

## 7. Get Conversation with Messages

```bash
curl http://localhost:8000/api/conversations/{conversation_id}
```

---

## 8. Delete Conversation

```bash
curl -X DELETE http://localhost:8000/api/conversations/{conversation_id}
```
