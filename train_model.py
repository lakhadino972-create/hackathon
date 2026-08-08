from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
from training_data import training_data

texts = [t[0] for t in training_data]
labels = [t[1] for t in training_data]

model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("classifier", MultinomialNB())
])

model.fit(texts, labels)

joblib.dump(model, "complaint_classifier.pkl")
print("Model trained and saved as complaint_classifier.pkl")