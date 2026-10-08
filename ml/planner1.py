import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = "../datasets/planner_dataset/prompt_decomposition_dataset_6000.csv"

MODEL_DIR = "../models"

TFIDF_DIR = os.path.join(MODEL_DIR, "tfidf")
EMBEDDING_DIR = os.path.join(MODEL_DIR, "embeddings")
HYBRID_DIR = os.path.join(MODEL_DIR, "hybrid")

os.makedirs(TFIDF_DIR, exist_ok=True)
os.makedirs(EMBEDDING_DIR, exist_ok=True)
os.makedirs(HYBRID_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_PATH)

df = df.dropna(subset=["prompt", "label"])

df["prompt"] = df["prompt"].astype(str)
df["label"] = df["label"].astype(int)

print("Dataset shape:", df.shape)

print("\nClass distribution:")
print(df["label"].value_counts())


X = df["prompt"]
y = df["label"]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate_model(name, model, X_test, y_test):

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    print("\n================================")
    print(name)
    print("================================")

    print("Accuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1 Score :", round(f1, 4))

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ============================================================
# MODEL 1
# TF-IDF + LOGISTIC REGRESSION
# ============================================================

print("\n\nTraining TF-IDF model...")

tfidf_model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
            max_features=50000
        )
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
           
        )
    )
])


tfidf_model.fit(
    X_train,
    y_train
)


tfidf_results = evaluate_model(
    "TF-IDF + Logistic Regression",
    tfidf_model,
    X_test,
    y_test
)


joblib.dump(
    tfidf_model,
    os.path.join(
        TFIDF_DIR,
        "tfidf_logistic.pkl"
    )
)


print("TF-IDF model saved.")


# ============================================================
# MODEL 2
# SENTENCE EMBEDDINGS + LOGISTIC REGRESSION
# ============================================================

print("\n\nLoading sentence transformer...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


print("Generating training embeddings...")

X_train_embeddings = embedding_model.encode(
    X_train.tolist(),
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)


print("Generating test embeddings...")

X_test_embeddings = embedding_model.encode(
    X_test.tolist(),
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)


print("Training embedding classifier...")

embedding_classifier = LogisticRegression(
    max_iter=2000,
    class_weight="balanced"
)


embedding_classifier.fit(
    X_train_embeddings,
    y_train
)




embedding_results = evaluate_model(
    "Sentence Embeddings + Logistic Regression",
    embedding_classifier,
    X_test_embeddings,
    y_test
)


# Save classifier
joblib.dump(
    embedding_classifier,
    os.path.join(
        EMBEDDING_DIR,
        "embedding_logistic.pkl"
    )
)



print("Embedding model saved.")

# ============================================================
# MODEL 3
# TF-IDF + SENTENCE EMBEDDINGS
# TF-IDF is reduced using TruncatedSVD
# ============================================================

print("\n\nCreating hybrid features...")


# ============================================================
# 1. TF-IDF
# ============================================================

tfidf_vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    max_features=30000
)


print("Generating TF-IDF features...")

X_train_tfidf = tfidf_vectorizer.fit_transform(
    X_train
)

X_test_tfidf = tfidf_vectorizer.transform(
    X_test
)


print(
    "Original TF-IDF training shape:",
    X_train_tfidf.shape
)


# ============================================================
# 2. REDUCE TF-IDF DIMENSIONS
# ============================================================

print("\nApplying TruncatedSVD...")

svd = TruncatedSVD(
    n_components=200,
    random_state=42
)


X_train_tfidf_reduced = svd.fit_transform(
    X_train_tfidf
)

X_test_tfidf_reduced = svd.transform(
    X_test_tfidf
)


print(
    "Reduced TF-IDF training shape:",
    X_train_tfidf_reduced.shape
)


print(
    "SVD explained variance:",
    round(
        svd.explained_variance_ratio_.sum(),
        4
    )
)


# ============================================================
# 3. NORMALIZE SVD FEATURES
# ============================================================

scaler = StandardScaler()

X_train_tfidf_reduced = scaler.fit_transform(
    X_train_tfidf_reduced
)

X_test_tfidf_reduced = scaler.transform(
    X_test_tfidf_reduced
)


# ============================================================
# 4. COMBINE TF-IDF + SENTENCE EMBEDDINGS
# ============================================================

print("\nCombining TF-IDF + sentence embeddings...")


X_train_hybrid = np.hstack([
    X_train_tfidf_reduced,
    X_train_embeddings
])


X_test_hybrid = np.hstack([
    X_test_tfidf_reduced,
    X_test_embeddings
])


print(
    "Final hybrid training shape:",
    X_train_hybrid.shape
)

print(
    "Final hybrid test shape:",
    X_test_hybrid.shape
)


# ============================================================
# 5. HYBRID CLASSIFIER
# ============================================================

print("\nTraining hybrid classifier...")


hybrid_classifier = LogisticRegression(
    max_iter=2000,
    class_weight="balanced"
)


hybrid_classifier.fit(
    X_train_hybrid,
    y_train
)


# ============================================================
# 6. EVALUATE
# ============================================================

hybrid_results = evaluate_model(
    "TF-IDF + SVD + Sentence Embeddings + Logistic Regression",
    hybrid_classifier,
    X_test_hybrid,
    y_test
)


# ============================================================
# 7. SAVE TF-IDF VECTORIZER
# ============================================================

joblib.dump(
    tfidf_vectorizer,
    os.path.join(
        HYBRID_DIR,
        "tfidf_vectorizer.pkl"
    )
)


# ============================================================
# 8. SAVE SVD
# ============================================================

joblib.dump(
    svd,
    os.path.join(
        HYBRID_DIR,
        "svd.pkl"
    )
)


# ============================================================
# 9. SAVE SCALER
# ============================================================

joblib.dump(
    scaler,
    os.path.join(
        HYBRID_DIR,
        "scaler.pkl"
    )
)


# ============================================================
# 10. SAVE CLASSIFIER
# ============================================================

joblib.dump(
    hybrid_classifier,
    os.path.join(
        HYBRID_DIR,
        "hybrid_logistic.pkl"
    )
)


print("\nHybrid model saved.")

# ============================================================
# MODEL 4
# TF-IDF + LINEAR SVM
# ============================================================

print("\n\nTraining TF-IDF + Linear SVM model...")


tfidf_svm_model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
            max_features=50000
        )
    ),

    (
        "classifier",
        LinearSVC(
            C=1.0,
            class_weight="balanced"
        )
    )
])


tfidf_svm_model.fit(
    X_train,
    y_train
)


tfidf_svm_results = evaluate_model(
    "TF-IDF + Linear SVM",
    tfidf_svm_model,
    X_test,
    y_test
)


joblib.dump(
    tfidf_svm_model,
    os.path.join(
        TFIDF_DIR,
        "tfidf_svm.pkl"
    )
)


print("TF-IDF + SVM model saved.")


# ============================================================
# MODEL 5
# TF-IDF + XGBOOST
# ============================================================

print("\n\nTraining TF-IDF + XGBoost model...")


# Generate TF-IDF features

tfidf_xgb_vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    max_features=10000
)


X_train_tfidf_xgb = tfidf_xgb_vectorizer.fit_transform(
    X_train
)

X_test_tfidf_xgb = tfidf_xgb_vectorizer.transform(
    X_test
)


print(
    "TF-IDF XGBoost training shape:",
    X_train_tfidf_xgb.shape
)


# XGBoost classifier

tfidf_xgb_classifier = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)


tfidf_xgb_classifier.fit(
    X_train_tfidf_xgb,
    y_train
)


tfidf_xgb_results = evaluate_model(
    "TF-IDF + XGBoost",
    tfidf_xgb_classifier,
    X_test_tfidf_xgb,
    y_test
)


# Save vectorizer

joblib.dump(
    tfidf_xgb_vectorizer,
    os.path.join(
        TFIDF_DIR,
        "tfidf_xgb_vectorizer.pkl"
    )
)


# Save classifier

joblib.dump(
    tfidf_xgb_classifier,
    os.path.join(
        TFIDF_DIR,
        "tfidf_xgboost.pkl"
    )
)


print("TF-IDF + XGBoost model saved.")

# ============================================================
# MODEL 6
# SENTENCE EMBEDDINGS + LINEAR SVM
# ============================================================

print("\n\nTraining Sentence Embeddings + Linear SVM...")


embedding_svm_classifier = LinearSVC(
    C=1.0,
    class_weight="balanced"
)


embedding_svm_classifier.fit(
    X_train_embeddings,
    y_train
)


embedding_svm_results = evaluate_model(
    "Sentence Embeddings + Linear SVM",
    embedding_svm_classifier,
    X_test_embeddings,
    y_test
)


joblib.dump(
    embedding_svm_classifier,
    os.path.join(
        EMBEDDING_DIR,
        "embedding_svm.pkl"
    )
)


print("Embedding SVM model saved.")


# ============================================================
# MODEL 7
# SENTENCE EMBEDDINGS + XGBOOST
# ============================================================

print("\n\nTraining Sentence Embeddings + XGBoost...")


embedding_xgb_classifier = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)


embedding_xgb_classifier.fit(
    X_train_embeddings,
    y_train
)


embedding_xgb_results = evaluate_model(
    "Sentence Embeddings + XGBoost",
    embedding_xgb_classifier,
    X_test_embeddings,
    y_test
)


joblib.dump(
    embedding_xgb_classifier,
    os.path.join(
        EMBEDDING_DIR,
        "embedding_xgboost.pkl"
    )
)


print("Embedding XGBoost model saved.")

# ============================================================
# MODEL 8
# TF-IDF + SVD + SENTENCE EMBEDDINGS + XGBOOST
# ============================================================

print("\n\nTraining Hybrid + XGBoost...")

hybrid_xgb_classifier = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

hybrid_xgb_classifier.fit(
    X_train_hybrid,
    y_train
)

hybrid_xgb_results = evaluate_model(
    "TF-IDF + SVD + Embeddings + XGBoost",
    hybrid_xgb_classifier,
    X_test_hybrid,
    y_test
)

joblib.dump(
    hybrid_xgb_classifier,
    os.path.join(
        HYBRID_DIR,
        "hybrid_xgboost.pkl"
    )
)

print("Hybrid XGBoost model saved.")

# ============================================================
# FINAL COMPARISON
# ============================================================

results = pd.DataFrame([
    {
        "model": "TF-IDF + Logistic Regression",
        **tfidf_results
    },

    {
        "model": "Sentence Embeddings + Logistic Regression",
        **embedding_results
    },

    {
        "model": "TF-IDF + SVD + Embeddings + Logistic Regression",
        **hybrid_results
    },

    {
        "model": "TF-IDF + Linear SVM",
        **tfidf_svm_results
    },

    {
        "model": "TF-IDF + XGBoost",
        **tfidf_xgb_results
    },

    {
        "model": "Sentence Embeddings + Linear SVM",
        **embedding_svm_results
    },

    {
        "model": "Sentence Embeddings + XGBoost",
        **embedding_xgb_results
    },

    {
        "model": "TF-IDF + SVD + Embeddings + XGBoost",
        **hybrid_xgb_results
    }
])


print("\n\n============================================")
print("FINAL MODEL COMPARISON")
print("============================================")


print(
    results.sort_values(
        "f1",
        ascending=False
    ).to_string(index=False)
)


results.to_csv(
    os.path.join(
        MODEL_DIR,
        "model_comparison.csv"
    ),
    index=False
)


print("\nTraining completed.")