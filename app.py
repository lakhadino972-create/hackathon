"""
app.py
------
AI Smart Civic Services — Web Frontend (Streamlit)

This connects directly to the SAME backend you already built and tested:
  - database.py   (SQLite storage, queries, statistics)
  - classifier.py (AI classification using the trained model)

No changes were made to those files. This file just replaces the console
menu (project.py) with a browser-based interface, using the exact same
functions underneath.

Run with:
    python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd

from database import (
    init_db, add_complaint, get_all_complaints, get_complaint_by_id,
    update_status, get_category_counts, get_status_counts,
    filter_complaints, get_resolution_times
)
from classifier import classify_complaint

# ---------- Setup ----------
st.set_page_config(page_title="AI Smart Civic Services", page_icon="🏙️", layout="wide")
init_db()  # make sure the table exists

VALID_STATUSES = ["Open", "Assigned", "In Progress", "Resolved"]
VALID_CATEGORIES = ["Road", "Water", "Drainage", "Waste", "Electricity", "Safety"]

st.title("🏙️ AI Smart Civic Services")

# ---------- Tabs: Citizen view vs Admin view ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📝 Submit Complaint", "📋 Manage Complaints", "🔍 Search/Filter", "📊 Statistics"]
)

# ===================== TAB 1: SUBMIT (Citizen) =====================
with tab1:
    st.subheader("Submit a Complaint")

    with st.form("complaint_form", clear_on_submit=True):
        description = st.text_area(
            "Describe the problem *",
            placeholder="e.g. There is a large water leak near the main road.",
            height=120,
        )
        location = st.text_input("Location *", placeholder="e.g. Main Road, Hyderabad")
        image = st.file_uploader("Upload a photo (optional)", type=["png", "jpg", "jpeg"])

        submitted = st.form_submit_button("Submit Complaint", use_container_width=True)

        if submitted:
            if not description.strip():
                st.error("Please describe the problem.")
            elif not location.strip():
                st.error("Please enter a location.")
            else:
                image_path = None
                if image is not None:
                    import os
                    os.makedirs("uploads", exist_ok=True)
                    image_path = os.path.join("uploads", image.name)
                    with open(image_path, "wb") as f:
                        f.write(image.getbuffer())

                # --- This is where frontend calls backend ---
                category = classify_complaint(description.strip())
                complaint_id = add_complaint(description.strip(), location.strip(), image_path, category)

                st.success(f"✅ Complaint #{complaint_id} submitted!")
                st.info(f"🤖 AI-predicted category: **{category}**")

# ===================== TAB 2: MANAGE (Admin) =====================
with tab2:
    st.subheader("All Complaints")

    rows = get_all_complaints()
    if not rows:
        st.info("No complaints submitted yet.")
    else:
        df = pd.DataFrame([dict(r) for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Update a Complaint's Status")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            complaint_id = st.number_input("Complaint ID", min_value=1, step=1)
        with col2:
            new_status = st.selectbox("New Status", VALID_STATUSES)
        with col3:
            st.write("")
            st.write("")
            if st.button("Update Status", use_container_width=True):
                success = update_status(int(complaint_id), new_status)
                if success:
                    st.success(f"Complaint #{int(complaint_id)} updated to '{new_status}'.")
                    st.rerun()
                else:
                    st.error("No complaint found with that ID.")

# ===================== TAB 3: SEARCH / FILTER =====================
with tab3:
    st.subheader("Search & Filter Complaints")

    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox("Filter by Category", ["Any"] + VALID_CATEGORIES)
    with col2:
        status_filter = st.selectbox("Filter by Status", ["Any"] + VALID_STATUSES)

    category_arg = None if category_filter == "Any" else category_filter
    status_arg = None if status_filter == "Any" else status_filter

    results = filter_complaints(category_arg, status_arg)

    if not results:
        st.info("No complaints match this filter.")
    else:
        df = pd.DataFrame([dict(r) for r in results])
        st.dataframe(df, use_container_width=True, hide_index=True)

# ===================== TAB 4: STATISTICS =====================
with tab4:
    st.subheader("Complaint Statistics")

    total = len(get_all_complaints())
    if total == 0:
        st.info("No complaints yet — nothing to analyze.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**By Category**")
            category_counts = get_category_counts()
            cat_df = pd.DataFrame(category_counts.items(), columns=["Category", "Count"])
            st.bar_chart(cat_df.set_index("Category"))

        with col2:
            st.markdown("**By Status**")
            status_counts = get_status_counts()
            status_df = pd.DataFrame(status_counts.items(), columns=["Status", "Count"])
            st.bar_chart(status_df.set_index("Status"))

        st.divider()
        st.markdown("**Resolution Time (hours)**")

        resolution_hours = get_resolution_times()
        if len(resolution_hours) == 0:
            st.info("No resolved complaints yet — nothing to calculate.")
        else:
            import statistics as stats_module

            mean_val = stats_module.mean(resolution_hours)
            median_val = stats_module.median(resolution_hours)
            min_val = min(resolution_hours)
            max_val = max(resolution_hours)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", f"{mean_val:.2f} hrs")
            c2.metric("Median", f"{median_val:.2f} hrs")
            c3.metric("Min", f"{min_val:.2f} hrs")
            c4.metric("Max", f"{max_val:.2f} hrs")

            if len(resolution_hours) > 1:
                stdev_val = stats_module.stdev(resolution_hours)
                variance_val = stats_module.variance(resolution_hours)
                c5, c6 = st.columns(2)
                c5.metric("Std Deviation", f"{stdev_val:.2f} hrs")
                c6.metric("Variance", f"{variance_val:.2f}")