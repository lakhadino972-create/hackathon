import joblib

model = joblib.load("complaint_classifier.pkl")

def classify_complaint(description):
    category = model.predict([description])[0]
    return category