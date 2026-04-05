"""
FHIR Clinical Analytics Dashboard — Streamlit App.

Demonstrates population health analytics on Synthea FHIR data.
Run: streamlit run app/dashboard.py
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

st.set_page_config(page_title="FHIR Analytics", page_icon="🏥", layout="wide")
st.sidebar.title("🏥 FHIR Analytics")
st.sidebar.markdown("**Synthea FHIR R4 Population Health**")
page = st.sidebar.selectbox("Dashboard", ["Demographics", "Conditions", "Medications", "Encounters"])

# ── Generate synthetic data for demo ─────────────────────────────────────────
np.random.seed(42)
N_PATIENTS = 500

@st.cache_data
def generate_demo_data():
    ages = np.random.choice(
        list(range(0, 18)) + list(range(18, 65)) + list(range(65, 95)),
        N_PATIENTS, p=[0.15/18]*18 + [0.55/47]*47 + [0.30/30]*30
    )
    genders = np.random.choice(["male", "female"], N_PATIENTS, p=[0.49, 0.51])
    states = np.random.choice(["MA", "NY", "CA", "TX", "FL"], N_PATIENTS)

    conditions_list = [
        "Hypertension", "Type 2 Diabetes", "Hyperlipidemia", "Obesity",
        "Anxiety", "Depression", "Asthma", "COPD", "Coronary Artery Disease",
        "Osteoarthritis", "Chronic Kidney Disease", "Atrial Fibrillation",
    ]
    prevalences = [0.30, 0.15, 0.28, 0.22, 0.18, 0.16, 0.12, 0.08, 0.09, 0.20, 0.11, 0.07]

    cond_rows = []
    for pid in range(N_PATIENTS):
        for cond, prev in zip(conditions_list, prevalences):
            if np.random.random() < prev:
                cond_rows.append({"patient_id": pid, "condition": cond})
    cond_df = pd.DataFrame(cond_rows)

    meds_list = ["Atorvastatin", "Metformin", "Lisinopril", "Amlodipine",
                 "Omeprazole", "Levothyroxine", "Metoprolol", "Sertraline",
                 "Albuterol", "Gabapentin"]
    med_rows = []
    for pid in range(N_PATIENTS):
        n_meds = np.random.poisson(2)
        chosen = np.random.choice(meds_list, min(n_meds, len(meds_list)), replace=False)
        for med in chosen:
            med_rows.append({"patient_id": pid, "medication": med})
    med_df = pd.DataFrame(med_rows)

    enc_types = ["Outpatient", "Emergency", "Inpatient", "Wellness", "Urgent Care"]
    enc_rows = []
    for pid in range(N_PATIENTS):
        n_enc = np.random.poisson(3)
        for _ in range(n_enc):
            enc_rows.append({
                "patient_id": pid,
                "type": np.random.choice(enc_types, p=[0.45, 0.15, 0.10, 0.20, 0.10]),
                "year": np.random.choice([2020, 2021, 2022, 2023]),
            })
    enc_df = pd.DataFrame(enc_rows)

    return (
        pd.DataFrame({"patient_id": range(N_PATIENTS), "age": ages, "gender": genders, "state": states}),
        cond_df, med_df, enc_df
    )


patients, conditions, medications, encounters = generate_demo_data()

# ── Pages ─────────────────────────────────────────────────────────────────────
st.title("🏥 FHIR Clinical Analytics Dashboard")
st.markdown(f"**Population:** {len(patients)} synthetic patients (Synthea FHIR R4)")

if page == "Demographics":
    st.subheader("Patient Demographics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", len(patients))
    col2.metric("Mean Age", f"{patients['age'].mean():.1f}")
    col3.metric("% Female", f"{(patients['gender']=='female').mean()*100:.1f}%")
    col4.metric("% 65+", f"{(patients['age']>=65).mean()*100:.1f}%")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(patients, x="age", nbins=20, color="gender",
                           title="Age Distribution by Gender",
                           color_discrete_map={"male": "#42A5F5", "female": "#EF5350"})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        state_counts = patients["state"].value_counts().reset_index()
        state_counts.columns = ["state", "count"]
        fig2 = px.bar(state_counts, x="state", y="count", title="Patients by State",
                      color="count", color_continuous_scale="Blues")
        st.plotly_chart(fig2, use_container_width=True)

elif page == "Conditions":
    st.subheader("Condition Prevalence")
    cond_counts = conditions.groupby("condition").size().sort_values(ascending=False).reset_index(name="count")
    cond_counts["prevalence_pct"] = cond_counts["count"] / len(patients) * 100

    fig = px.bar(cond_counts, x="prevalence_pct", y="condition", orientation="h",
                 title="Condition Prevalence in Synthetic Population",
                 labels={"prevalence_pct": "Prevalence (%)", "condition": ""},
                 color="prevalence_pct", color_continuous_scale="Reds")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Comorbidity: top 2 co-occurring pairs
    st.subheader("Top Comorbidity Pairs")
    from itertools import combinations
    patient_conds = conditions.groupby("patient_id")["condition"].apply(list)
    pair_counts = {}
    for cond_list in patient_conds:
        for a, b in combinations(sorted(set(cond_list)), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    top_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:10]
    pair_df = pd.DataFrame([(f"{a} + {b}", c) for (a,b),c in top_pairs], columns=["Pair", "Count"])
    st.dataframe(pair_df)

elif page == "Medications":
    st.subheader("Medication Analytics")
    med_counts = medications.groupby("medication").size().sort_values(ascending=False).reset_index(name="prescriptions")
    fig = px.bar(med_counts, x="medication", y="prescriptions",
                 title="Top Prescribed Medications",
                 color="prescriptions", color_continuous_scale="Greens")
    st.plotly_chart(fig, use_container_width=True)

    n_meds = medications.groupby("patient_id").size()
    polypharmacy_rate = (n_meds >= 5).mean() * 100
    col1, col2 = st.columns(2)
    col1.metric("Polypharmacy Rate (≥5 meds)", f"{polypharmacy_rate:.1f}%")
    col2.metric("Mean Medications per Patient", f"{n_meds.mean():.1f}")

elif page == "Encounters":
    st.subheader("Healthcare Utilization")
    enc_type = encounters.groupby("type").size().reset_index(name="count")
    fig = px.pie(enc_type, names="type", values="count",
                 title="Encounter Type Distribution")
    st.plotly_chart(fig, use_container_width=True)

    enc_year = encounters.groupby("year").size().reset_index(name="count")
    fig2 = px.line(enc_year, x="year", y="count", markers=True,
                   title="Encounter Volume by Year")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.caption("FHIR Analytics · Synthea Synthetic Data · [GitHub](https://github.com/hollyakt/fhir-parser)")
