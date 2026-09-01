
"""
Planner Module
--------------
1. Uses the trained ML classifier to determine whether
   the prompt requires decomposition.
2. If decomposition is required, calls the LLM to generate
   a DAG of subtasks.
3. If decomposition is not required, returns a single-node DAG.
"""


import json
from pathlib import Path

import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

from app.providers.factory import get_provider


# ============================================================
# PATHS
# ============================================================



PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = PROJECT_ROOT / "models" / "hybrid"

TFIDF_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
SVD_PATH = MODEL_DIR / "svd.pkl"
CLASSIFIER_PATH = MODEL_DIR / "hybrid_logistic.pkl"


# ============================================================
# LOAD ML MODELS
# ============================================================

print("Loading planner ML models...")

tfidf_vectorizer = joblib.load(TFIDF_PATH)

svd = joblib.load(SVD_PATH)

classifier = joblib.load(CLASSIFIER_PATH)


# Sentence Transformer
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Planner ML models loaded successfully.")


# ============================================================
# LLM DAG PROMPT
# ============================================================
DAG_PROMPT = """
You are an intelligent task planner.

The user's prompt has already been classified by an ML
classifier as requiring decomposition.

Your task is to break the user's request into a Directed
Acyclic Graph (DAG) of meaningful subtasks.

For every subtask, you must also identify the expected
OUTPUT TYPE of that subtask.

The allowed output types are EXACTLY:

* "text"   : the task produces textual output
* "image"  : the task produces an image
* "video"  : the task produces a video

IMPORTANT:

* "output_type" refers to what the task PRODUCES, not what it consumes.
* For example, analyzing an uploaded image and explaining it produces TEXT, so output_type should be "text".
* Creating an image from a textual description produces IMAGE.
* Creating a video from a prompt produces VIDEO.
* Never use any output type other than "text", "image", or "video".

IMPORTANT RULES:

1. Create only the necessary subtasks.
2. Each node should represent one concrete operation.
3. Identify dependencies between tasks.
4. A task can depend on zero or more previous tasks.
5. Tasks with no dependency can execute independently.
6. If two tasks can be executed in parallel, do not make one
   unnecessarily depend on the other.
7. Do not create unnecessary intermediate tasks.
8. The graph MUST be acyclic.
9. The final task should produce the final requested result
   whenever appropriate.
10. Every node MUST contain an "output_type" field.
11. "output_type" MUST be exactly one of:
    "text", "image", "video".
12. Return ONLY valid JSON.
13. Do not include markdown.
14. Do not include explanations outside the JSON.

Return exactly this format:

{
"nodes": [
{
"id": "task_1",
"task": "Description of the task",
"output_type": "text",
"depends_on": []
},
{
"id": "task_2",
"task": "Description of the task",
"output_type": "image",
"depends_on": ["task_1"]
}
]
}

Example 1:

User prompt:
"Research the best laptops under 80000, compare their
specifications and recommend the best one for programming."

Output:

{
"nodes": [
{
"id": "task_1",
"task": "Research laptops under 80000 suitable for programming",
"output_type": "text",
"depends_on": []
},
{
"id": "task_2",
"task": "Collect and compare specifications of the shortlisted laptops",
"output_type": "text",
"depends_on": ["task_1"]
},
{
"id": "task_3",
"task": "Check current prices of the shortlisted laptops",
"output_type": "text",
"depends_on": ["task_1"]
},
{
"id": "task_4",
"task": "Recommend the best laptop based on specifications and price",
"output_type": "text",
"depends_on": ["task_2", "task_3"]
}
]
}

Example 2:

User prompt:
"Research the history of the Eiffel Tower and create an
illustrated video explaining its history."

Output:

{
"nodes": [
{
"id": "task_1",
"task": "Research the history and important events related to the Eiffel Tower",
"output_type": "text",
"depends_on": []
},
{
"id": "task_2",
"task": "Create suitable illustrations based on the researched history",
"output_type": "image",
"depends_on": ["task_1"]
},
{
"id": "task_3",
"task": "Create an explanatory video using the researched information and illustrations",
"output_type": "video",
"depends_on": ["task_1", "task_2"]
}
]
}

Example 3:

User prompt:
"Analyze this image and explain what is happening in it."

Output:

{
"nodes": [
{
"id": "task_1",
"task": "Analyze the uploaded image and explain what is happening in it",
"output_type": "text",
"depends_on": []
}
]
}

Example 4:

User prompt:
"Generate an image of a futuristic city and then create
a video showing the city from different angles."

Output:

{
"nodes": [
{
"id": "task_1",
"task": "Generate an image of a futuristic city",
"output_type": "image",
"depends_on": []
},
{
"id": "task_2",
"task": "Create a video showing the futuristic city from different angles using the generated image",
"output_type": "video",
"depends_on": ["task_1"]
}
]
}

User prompt:
{prompt}
"""


# ============================================================
# ML CLASSIFICATION
# ============================================================

def classify_decomposition(prompt: str) -> bool:
    """
    Predict whether the prompt requires decomposition.

    Returns:
        True  -> decomposition required
        False -> no decomposition required

    Feature pipeline:

        Prompt
          |
          +--> TF-IDF --> SVD ----+
          |                       |
          +--> Sentence Embedding-+
                                  |
                                  v
                            Hybrid Features
                                  |
                                  v
                         Logistic Regression
    """

    # --------------------------------------------------------
    # 1. TF-IDF
    # --------------------------------------------------------

    tfidf_features = tfidf_vectorizer.transform(
        [prompt]
    )

    # --------------------------------------------------------
    # 2. Truncated SVD
    # --------------------------------------------------------

    tfidf_svd_features = svd.transform(
        tfidf_features
    )

    # --------------------------------------------------------
    # 3. Sentence Embedding
    # --------------------------------------------------------

    embedding_features = embedding_model.encode(
        [prompt],
        normalize_embeddings=True
    )

    # --------------------------------------------------------
    # 4. Combine
    # --------------------------------------------------------

    hybrid_features = np.hstack(
        [
            tfidf_svd_features,
            embedding_features
        ]
    )

    # --------------------------------------------------------
    # 5. ML Prediction
    # --------------------------------------------------------

    prediction = classifier.predict(
        hybrid_features
    )[0]

    return bool(prediction)


# ============================================================
# DAG VALIDATION
# ============================================================

def validate_dag(nodes: list[dict]) -> bool:
    """
    Validate the DAG returned by the LLM.

    Checks:

    - nodes exist
    - every node has an ID
    - every node has a task
    - dependency IDs exist
    - no self dependency
    - graph contains no cycle
    """

    if not nodes:
        return False

    # --------------------------------------------------------
    # Collect node IDs
    # --------------------------------------------------------

    node_ids = set()

    for node in nodes:

        node_id = node.get("id")

        task = node.get("task")

        if not node_id or not task:
            return False

        if node_id in node_ids:
            return False

        node_ids.add(node_id)

    # --------------------------------------------------------
    # Validate dependencies
    # --------------------------------------------------------

    graph = {}

    for node in nodes:

        node_id = node["id"]

        dependencies = node.get(
            "depends_on",
            []
        )

        if not isinstance(dependencies, list):
            return False

        graph[node_id] = dependencies

        for dependency in dependencies:

            # Dependency must exist
            if dependency not in node_ids:
                return False

            # No self dependency
            if dependency == node_id:
                return False

    # --------------------------------------------------------
    # Cycle Detection
    # --------------------------------------------------------

    visited = set()
    recursion_stack = set()

    def has_cycle(node_id):

        if node_id in recursion_stack:
            return True

        if node_id in visited:
            return False

        visited.add(node_id)
        recursion_stack.add(node_id)

        for dependency in graph[node_id]:

            if has_cycle(dependency):
                return True

        recursion_stack.remove(node_id)

        return False

    for node_id in node_ids:

        if has_cycle(node_id):
            return False

    return True


# ============================================================
# EXTRACT JSON
# ============================================================

def extract_json(raw_response: str) -> dict:
    """
    Extract JSON from an LLM response.

    Handles both:

    {
        "nodes": [...]
    }

    and markdown code blocks.
    """

    text = raw_response.strip()

    # --------------------------------------------------------
    # Remove markdown code block
    # --------------------------------------------------------

    if "```" in text:

        parts = text.split("```")

        if len(parts) >= 2:

            text = parts[1].strip()

            # Remove "json" language identifier
            if text.lower().startswith("json"):

                text = text[4:].strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    return json.loads(text)


# ============================================================
# MAIN PLANNER
# ============================================================

async def plan(prompt: str) -> dict:
    

    # ========================================================
    # STEP 1
    # ML CLASSIFICATION
    # ========================================================

    needs_decomposition = classify_decomposition(
        prompt
    )

    print(
        f"[Planner ML] "
        f"needs_decomposition={needs_decomposition}"
    )


    # ========================================================
    # STEP 2
    # NO DECOMPOSITION
    # ========================================================

    if not needs_decomposition:

        print(
            "[Planner] No decomposition required."
        )

        return {
            "needs_decomposition": False,

            "nodes": [
                {
                    "id": "task_1",
                    "task": prompt,
                    "depends_on": []
                }
            ]
        }


    # ========================================================
    # STEP 3
    # DECOMPOSITION REQUIRED
    # ========================================================

    print(
        "[Planner] Decomposition required. "
        "Calling LLM..."
    )

    provider = get_provider(
        "openrouter"
    )

    full_prompt = DAG_PROMPT.format(
        prompt=prompt
    )


    try:

        # ----------------------------------------------------
        # Call LLM
        # ----------------------------------------------------

        raw_response = await provider.generate(
            full_prompt
        )

        print(
            "[Planner] LLM response received."
        )


        # ----------------------------------------------------
        # Extract JSON
        # ----------------------------------------------------

        data = extract_json(
            raw_response
        )


        # ----------------------------------------------------
        # Extract nodes
        # ----------------------------------------------------

        nodes = data.get(
            "nodes",
            []
        )


        # ----------------------------------------------------
        # Validate DAG
        # ----------------------------------------------------

        if not validate_dag(nodes):

            raise ValueError(
                "LLM returned an invalid DAG."
            )


        print(
            f"[Planner] Valid DAG generated "
            f"with {len(nodes)} nodes."
        )


        return {
            "needs_decomposition": True,
            "nodes": nodes
        }


    except Exception as e:

        print(
            f"[Planner ERROR] {e}"
        )


        # ====================================================
        # FALLBACK
        # ====================================================

        print(
            "[Planner] Falling back to single task."
        )

        return {
            "needs_decomposition": False,

            "nodes": [
                {
                    "id": "task_1",
                    "task": prompt,
                    "depends_on": []
                }
            ]
        }