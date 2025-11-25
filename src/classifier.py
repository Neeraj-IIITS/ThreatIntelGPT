# src/classifier.py
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import pickle


def train_classifier(
    texts: List[str],
    labels: List[str],
    model_path: str = "clf_model.pkl",
    vec_path: str = "tfidf_vec.pkl"
) -> Tuple[TfidfVectorizer, LogisticRegression]:
    """
    Train a simple TF-IDF + Logistic Regression classifier.
    labels could be: phishing, ransomware, vuln, general, etc.
    """
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000
    )
    X = vectorizer.fit_transform(texts)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, labels)

    # save to disk
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)

    return vectorizer, clf


def load_classifier(
    model_path: str = "clf_model.pkl",
    vec_path: str = "tfidf_vec.pkl"
) -> Tuple[TfidfVectorizer, LogisticRegression]:
    import pickle
    with open(vec_path, "rb") as f:
        vectorizer = pickle.load(f)
    with open(model_path, "rb") as f:
        clf = pickle.load(f)
    return vectorizer, clf


def predict_category(text: str, vectorizer, clf) -> str:
    X = vectorizer.transform([text])
    pred = clf.predict(X)
    return pred[0]


def evaluate_classifier(
    train_texts: List[str],
    train_labels: List[str],
    test_texts: List[str],
    test_labels: List[str]
):
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, train_labels)

    y_pred = clf.predict(X_test)
    print("Accuracy:", accuracy_score(test_labels, y_pred))
    print(classification_report(test_labels, y_pred))

    return vectorizer, clf
