import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report
import joblib


data = pd.read_csv("data/commands.csv")

X = data["sentence"]
y = data["intent"]


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 3),
        stop_words="english",
        sublinear_tf=True
    )),
    ("clf", LinearSVC())
])

params = {
    "tfidf__min_df": [1, 2],
    "clf__C": [0.5, 1.0, 2.0, 5.0]
}

grid = GridSearchCV(
    pipeline,
    params,
    cv=5,
    n_jobs=-1
)

grid.fit(X_train, y_train)

best_model = grid.best_estimator_

pred = best_model.predict(X_test)
acc = accuracy_score(y_test, pred)

print("Best Parameters:", grid.best_params_)
print("Model Accuracy:", acc)
print("\nClassification Report:\n", classification_report(y_test, pred))

joblib.dump(best_model, "core/intent_model.pkl")
print("Model saved as core/intent_model.pkl")
