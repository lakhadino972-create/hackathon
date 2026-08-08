# AI Smart Civic Services — Civic Complaint Management System

**Batch:** 4 — Statistics
**Type:** AI-powered civic complaint management console application

---

## 1. Problem

Citizens regularly face local infrastructure problems — broken streetlights,
overflowing garbage, damaged roads, water leaks, drainage issues, and unsafe
public areas. Reporting these problems is often fragmented, and service teams
struggle to figure out which complaints are urgent and which department
should handle them.

This project turns an unstructured citizen complaint into structured,
actionable information: the system automatically classifies the complaint
into a category, stores it with full details, and gives administrators
tools to manage and analyze complaint data over time.

**Users:**
- **Citizens** — submit complaints about local problems.
- **Service team / administrators** — view, filter, update status, and
  analyze complaint trends.

---

## 2. Features

- **Complaint submission** with input validation (description, location,
  optional photo path).
- **AI-powered classification** — every complaint is automatically sorted
  into a category (Road, Water, Drainage, Waste, Electricity, Safety) using
  a trained machine learning model.
- **Storage** — every complaint is saved to a local SQLite database.
- **Complaint management** — view all complaints, view a single complaint by
  ID, and update its status (Open → Assigned → In Progress → Resolved).
- **Search & filter** — find complaints by category and/or status.
- **Statistics & analytics**:
  - Category frequency distribution (counts + percentages)
  - Status frequency distribution (counts + percentages)
  - Most commonly reported problem type
  - Resolution time statistics: mean, median, minimum, maximum, standard
    deviation, and variance (calculated from submission → resolved
    timestamps)

---

## 3. AI Technology

**Approach:** Supervised text classification using scikit-learn.

| Stage | Detail |
|---|---|
| **Input** | The raw complaint description text typed by the citizen |
| **Processing** | TF-IDF vectorization → Multinomial Naive Bayes classifier |
| **Output** | A predicted category: Road, Water, Drainage, Waste, Electricity, or Safety |
| **Training data** | A small hand-written labeled dataset (~30 example complaints across 6 categories), created specifically for this project since no public labeled dataset of local civic complaints was available |

**Why this approach:** TF-IDF + Naive Bayes is lightweight, requires no GPU
or heavy downloads, trains in under a second, and is fully explainable —
appropriate given the project's time and environment constraints, while
still being a genuinely trained ML model (not a hardcoded rule engine).

**Limitations (honestly reported, as required by the spec):**
- The model is trained on a small dataset (~30 examples), so accuracy is
  reasonable but not perfect. Some ambiguous or oddly worded complaints can
  be misclassified — for example, a complaint mentioning "streetlight" was
  initially misclassified as "Road" until more training examples were added
  to disambiguate Road vs. Electricity vocabulary.
- The model has no way to say "I'm not sure" — it always returns its best
  guess among the trained categories, even for an unfamiliar complaint.
- More training examples per category would improve reliability further.

---

## 4. Data Model

| Field | Description |
|---|---|
| `complaint_id` | Unique auto-generated ID |
| `description` | Citizen's complaint text |
| `category` | AI-predicted category |
| `location` | Complaint location (entered by citizen) |
| `date` | Submission timestamp (auto-captured) |
| `status` | Open / Assigned / In Progress / Resolved |
| `resolved_date` | Timestamp when status changed to Resolved (auto-captured, used for resolution-time statistics) |
| `image_path` | Path to an optional uploaded photo |

---

## 5. Architecture

```
Citizen (console input)
        │
        ▼
  project.py  ──────────────►  classifier.py
  (menu, validation,           (loads trained model,
   orchestration)                predicts category)
        │                              │
        ▼                              │
  database.py  ◄─────────────────────────
  (SQLite storage, queries,
   statistics calculations)
        │
        ▼
  civic_complaints.db
```

- **`project.py`** — the entry point. Handles the interactive menu, collects
  and validates citizen input, and calls the AI and database layers.
- **`classifier.py`** — loads the trained model (`complaint_classifier.pkl`)
  and exposes `classify_complaint(description)`.
- **`train_model.py`** / **`training_data.py`** — used once, offline, to
  train and save the classification model.
- **`database.py`** — all SQLite operations: creating the table, inserting,
  updating, filtering, and computing statistics.

---

## 6. Setup & Usage

**Requirements:** Python 3.10+, `scikit-learn`, `joblib`

```bash
pip install scikit-learn joblib
```

**1. Train the AI model (only needs to be done once):**
```bash
python train_model.py
```
This creates `complaint_classifier.pkl`.

**2. Run the application:**
```bash
python project.py
```

**3. Use the menu:**
```
1. Submit a complaint
2. View all complaints
3. View a single complaint
4. Update complaint status
5. Show statistics
6. Search/filter complaints
7. Exit
```

---

## 7. AI Testing Evidence

Sample tested inputs and predicted categories:

| Complaint text | Predicted category | Correct? |
|---|---|---|
| "There is a huge pothole on the main road" | Road | ✅ |
| "No water supply in our area for three days" | Water | ✅ |
| "Streetlight not working near my house" | Road → later corrected to Electricity after retraining | ⚠️ initially wrong, fixed |
| "Garbage bin is overflowing and not collected" | Waste | ✅ |

This confirms the model works for clearly-worded complaints, and documents
a real limitation (ambiguous vocabulary between categories) along with how
it was addressed (adding more targeted training examples).

---

## 8. Status

This is a working prototype covering: complaint submission, AI
classification, storage, management, search/filtering, and statistics. A
graphical (web) interface and public deployment are the next planned steps.
