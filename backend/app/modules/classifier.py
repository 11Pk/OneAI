# """
# Task Classifier Module
# ----------------------
# Categorizes each task into one of: coding, research, writing, analysis, general.

# Uses an LLM with a simple classification prompt.
# """

# import json

# from app.providers.factory import get_provider

# # Valid categories the router understands
# CATEGORIES = ["coding", "research", "writing", "analysis", "general"]

# CLASSIFIER_PROMPT = """Classify the following task into exactly ONE category.

# Categories:
# - coding: programming, debugging, code review, algorithms, software development
# - research: finding information, facts, explanations, learning topics
# - writing: essays, emails, creative writing, content creation
# - analysis: data analysis, comparisons, evaluations, reasoning
# - general: anything that doesn't fit above

# Respond ONLY with valid JSON:
# {{"category": "coding"}}

# Task:
# {task}
# """


# async def classify(task: str) -> str:
#     """
#     Return the category string for a task.
#     Defaults to 'general' if classification fails.
#     """
#     provider = get_provider("openrouter")
#     full_prompt = CLASSIFIER_PROMPT.format(task=task)

#     try:
#         raw = await provider.generate(full_prompt)
#         text = raw.strip()
#         if "```" in text:
#             text = text.split("```")[1]
#             if text.startswith("json"):
#                 text = text[4:]
#         data = json.loads(text.strip())
#         category = data.get("category", "general").lower()

#         if category not in CATEGORIES:
#             return "general"
#         return category

#     except (json.JSONDecodeError, KeyError):
#         return "general"














#using ML To classify

"""
Classifies each task into one of:
coding, research, writing, analysis, general

ML approach:
TF-IDF + Logistic Regression
"""

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# Valid categories understood by OneAI
CATEGORIES = [
    "coding",
    "research",
    "writing",
    "analysis",
    "general"
]

# 1. Load Dataset


df = pd.read_csv("data/classifier_dataset.csv")

X = df["text"]
y = df["category"]


# 2. Split Dataset

#80 percent of the data is used for training
#each tiem the data is split into the same sets
#equal proportions of eachc y category is there
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# 3. Convert Text → TF-IDF Vectors
#removes the english stop words and maximum one-two word combinations are considered for the vectorization
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2)
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)



# 4. Train ML Classifier


model = LogisticRegression(
    max_iter=1000
)

model.fit(X_train_tfidf, y_train)


# 5. Evaluate Model


predictions = model.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, predictions)

print("OneAI TF-IDF Classifier")


print(f"Accuracy: {accuracy:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, predictions))


# 6. OneAI Classifier Function

async def classify(task: str) -> str:

    # Convert the new task into the SAME TF-IDF space
    task_vector = vectorizer.transform([task])

    # Predict category
    category = model.predict(task_vector)[0]

    # Safety check
    if category not in CATEGORIES:
        return "general"

    return category