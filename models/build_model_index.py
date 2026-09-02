import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

REGISTRY_PATH = BASE_DIR / "model_registery.json"
INDEX_PATH = BASE_DIR / "model_description.faiss"
IDS_PATH = BASE_DIR / "model_ids.json"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index():
    registry = load_registry()
    models = registry["models"]

    documents = []
    vector_to_model_id = []

    for model in models:
        m_id = model["id"]

        # 1. Main concise description
        desc = model.get("description", "").strip()
        if desc:
            documents.append(f"Model capable of: {desc}")
            vector_to_model_id.append(m_id)

        # 2. Individual capability items
        for cap in model.get("capabilities", []):
            documents.append(f"Model capability: {cap}")
            vector_to_model_id.append(m_id)

        # 3. Individual 'good_for' action items (Highest signal)
        for gf in model.get("good_for", []):
            documents.append(f"Model good for: {gf}")
            vector_to_model_id.append(m_id)

    print(f"Generated {len(documents)} anchor vectors across {len(models)} models.")

    # Load embedding model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("Generating embeddings...")
    embeddings = embedding_model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, str(INDEX_PATH))

    # Save vector -> model_id map
    with open(IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(vector_to_model_id, f, indent=2)

    print("\nIndex created successfully!")
    print(f"Total Vectors in FAISS: {index.ntotal}")


if __name__ == "__main__":
    build_index()