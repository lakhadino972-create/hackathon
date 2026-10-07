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
# ===================== TAB 4: STATISTICS =====================
# ===================== TAB 4: STATISTICS =====================
with tab4:
    st.subheader("Complaint Statistics")

    total = len(get_all_complaints())
    if total == 0:
        st.info("No complaints yet — nothing to analyze.")
    else:
        import matplotlib.pyplot as plt

        col1, col2 = st.columns(2)

        # ---- Pie chart: Category distribution ----
        with col1:
            st.markdown("**What kind of problems are people reporting?**")
            category_counts = get_category_counts()
            fig1, ax1 = plt.subplots()
            ax1.pie(
                category_counts.values(),
                labels=category_counts.keys(),
                autopct="%1.0f%%",
                startangle=90,
            )
            ax1.axis("equal")
            st.pyplot(fig1)

        # ---- Pie chart: Status distribution ----
        with col2:
            st.markdown("**Where are complaints in the process?**")
            status_counts = get_status_counts()
            fig2, ax2 = plt.subplots()
            colors = {"Open": "#ff6b6b", "Assigned": "#feca57", "In Progress": "#54a0ff", "Resolved": "#1dd1a1"}
            pie_colors = [colors.get(s, "#cccccc") for s in status_counts.keys()]
            ax2.pie(
                status_counts.values(),
                labels=status_counts.keys(),
                autopct="%1.0f%%",
                startangle=90,
                colors=pie_colors,
            )
            ax2.axis("equal")
            st.pyplot(fig2)

        st.divider()

        # ---- Simple headline numbers ----
        most_common_category = category_counts.most_common(1)[0]
        resolved_count = status_counts.get("Resolved", 0)
        open_count = total - resolved_count

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Complaints", total)
        c2.metric("Most Common Problem", most_common_category[0])
        c3.metric("Still Open/In Progress", open_count)

        st.divider()

        # ---- Resolution time, explained in plain language ----
        st.markdown("**How long does it take to resolve a complaint?**")
        resolution_hours = get_resolution_times()

        if len(resolution_hours) == 0:
            st.info("No complaints have been marked 'Resolved' yet, so there's no timing data.")
        else:
            import statistics as stats_module

            mean_val = stats_module.mean(resolution_hours)
            median_val = stats_module.median(resolution_hours)

            # Convert to a friendlier unit if the numbers are small/large
            def friendly_time(hours):
                if hours < 1:
                    return f"{hours * 60:.0f} minutes"
                elif hours < 24:
                    return f"{hours:.1f} hours"
                else:
                    return f"{hours / 24:.1f} days"

            st.write(f"On average, a complaint takes **{friendly_time(mean_val)}** to resolve.")
            st.write(f"Half of all resolved complaints were closed within **{friendly_time(median_val)}**.")

            with st.expander("See detailed numbers (min, max, std deviation, variance)"):
                min_val = min(resolution_hours)
                max_val = max(resolution_hours)
                c1, c2 = st.columns(2)
                c1.metric("Fastest resolution", friendly_time(min_val))
                c2.metric("Slowest resolution", friendly_time(max_val))

                if len(resolution_hours) > 1:
                    stdev_val = stats_module.stdev(resolution_hours)
                    variance_val = stats_module.variance(resolution_hours)
                    st.write(f"Standard Deviation: {stdev_val:.2f} hours (how spread out resolution times are)")
                    st.write(f"Variance: {variance_val:.2f}")