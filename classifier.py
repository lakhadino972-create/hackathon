"""
classifier.py
-------------
Loads the trained complaint classification model and exposes
classify_complaint(description) -> category.

The model path is built from this file's own location, so it works no matter
which folder the app is launched from (local machine or Streamlit Cloud).
"""

import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "complaint_classifier.pkl")

model = joblib.load(MODEL_PATH)


def classify_complaint(description):
    """Return the predicted category (e.g. 'Road') for a complaint text."""
    category = model.predict([description])[0]
    return str(category)
