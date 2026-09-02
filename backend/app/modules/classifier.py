import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

REGISTRY_PATH = BASE_DIR / "models" / "model_registery.json"
INDEX_PATH = BASE_DIR / "models" / "model_description.faiss"
IDS_PATH = BASE_DIR / "models" / "model_ids.json"

# Load metadata
with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)
models = registry["models"]

with open(IDS_PATH, "r", encoding="utf-8") as f:
    vector_to_model_id = json.load(f)

index = faiss.read_index(str(INDEX_PATH))
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

MIN_SIMILARITY_THRESHOLD = 0.20


def get_allowed_models(output_type):
    return [
        m for m in models 
        if output_type in m.get("output_modalities", [])
    ]


def get_top_models(subtask, output_type="text", k=3):
    allowed_models = get_allowed_models(output_type)
    if not allowed_models:
        return []

    allowed_ids = {m["id"] for m in allowed_models}

    # Format query directly as an action target
    formatted_query = f"Model good for: {subtask}"

    query_embedding = embedding_model.encode(
        [formatted_query],
        normalize_embeddings=True
    )
    query_embedding = np.asarray(query_embedding, dtype="float32")
    faiss.normalize_L2(query_embedding)

    # Search top 25 vectors to cover multi-vector hits
    search_k = min(index.ntotal, 25)
    scores, indices = index.search(query_embedding, search_k)

    # Max-pooling: collect highest similarity per model
    best_model_scores = {}

    for score, index_pos in zip(scores[0], indices[0]):
        if index_pos < 0:
            continue

        model_id = vector_to_model_id[index_pos]

        if model_id not in allowed_ids:
            continue

        similarity = float(score)

        # Store max similarity for this model
        if model_id not in best_model_scores or similarity > best_model_scores[model_id]:
            best_model_scores[model_id] = similarity

    # Sort models by highest score
    sorted_models = sorted(
        best_model_scores.items(), 
        key=lambda item: item[1], 
        reverse=True
    )[:k]

    results = []
    for model_id, score in sorted_models:
        results.append({
            "model_id": model_id,
            "similarity_score": score,
            "match_percentage": f"{round(score * 100, 2)}%"
        })
    if not results or results[0]["similarity_score"] < MIN_SIMILARITY_THRESHOLD:
      return [{
        "model_id": "gemini-flash",
        "similarity_score": 0.0,
        "match_percentage": "Fallback (Low Confidence)"
    }]

    return results


if __name__ == "__main__":
    subtask = "Please proofread this short email, fix any grammar or spelling mistakes, and rewrite it to sound slightly more polite and professional."

    result = get_top_models(subtask, output_type="text", k=3)
    print(json.dumps(result, indent=4))