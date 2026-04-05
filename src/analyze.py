"""
Population health analytics from parsed FHIR data.
"""

from pathlib import Path
from typing import Dict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_parsed_data(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load parsed CSV files from parse.py output."""
    data_dir = Path(data_dir)
    dfs = {}
    for csv_path in data_dir.glob("*.csv"):
        name = csv_path.stem.title()
        dfs[name] = pd.read_csv(csv_path)
    return dfs


def top_conditions(conditions: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Return top N conditions by prevalence."""
    active = conditions[conditions["clinical_status"] == "active"]
    return (active.groupby("display")
            .size()
            .sort_values(ascending=False)
            .head(n)
            .reset_index(name="count"))


def top_medications(meds: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Return top N active medications by prescription count."""
    active = meds[meds["status"] == "active"]
    return (active.groupby("med_name")
            .size()
            .sort_values(ascending=False)
            .head(n)
            .reset_index(name="count"))


def comorbidity_matrix(conditions: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Compute co-occurrence matrix of top N conditions."""
    top = top_conditions(conditions, top_n)["display"].tolist()
    cond_filtered = conditions[conditions["display"].isin(top)]
    patient_conds = cond_filtered.groupby("patient_id")["display"].apply(set)

    matrix = pd.DataFrame(0, index=top, columns=top)
    for cond_set in patient_conds:
        cond_list = [c for c in cond_set if c in top]
        for i, c1 in enumerate(cond_list):
            for c2 in cond_list:
                matrix.loc[c1, c2] += 1
    np.fill_diagonal(matrix.values, 0)
    return matrix


def polypharmacy_analysis(meds: pd.DataFrame, patients: pd.DataFrame) -> pd.DataFrame:
    """Identify patients on 5+ concurrent active medications (polypharmacy)."""
    active = meds[meds["status"] == "active"]
    med_counts = active.groupby("patient_id")["med_name"].count().reset_index(name="n_meds")
    if patients is not None:
        med_counts = med_counts.merge(patients[["patient_id", "age", "gender"]],
                                       on="patient_id", how="left")
    med_counts["polypharmacy"] = med_counts["n_meds"] >= 5
    return med_counts


def plot_demographics(patients: pd.DataFrame, output_dir: Path):
    """Age/sex distribution plot."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(patients["age"].dropna(), bins=20, color="#1E88E5", alpha=0.85, edgecolor="white")
    axes[0].set_xlabel("Age (years)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Patient Age Distribution")
    axes[0].axvline(patients["age"].median(), color="red", linestyle="--",
                     label=f"Median: {patients['age'].median():.0f}")
    axes[0].legend()

    gender_counts = patients["gender"].value_counts()
    axes[1].pie(gender_counts.values, labels=gender_counts.index,
                autopct="%1.1f%%", colors=["#42A5F5", "#EF5350", "#66BB6A"])
    axes[1].set_title("Gender Distribution")
    plt.tight_layout()
    plt.savefig(str(output_dir / "demographics.png"), bbox_inches="tight", dpi=150)
    plt.close()


def plot_top_conditions(conditions: pd.DataFrame, output_dir: Path):
    """Horizontal bar chart of top conditions."""
    top = top_conditions(conditions, 15)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(top)))
    ax.barh(range(len(top)), top["count"].values, color=colors[::-1], alpha=0.85)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["display"].values, fontsize=9)
    ax.set_xlabel("Number of Active Cases")
    ax.set_title("Top 15 Conditions by Prevalence (Active)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(str(output_dir / "top_conditions.png"), bbox_inches="tight", dpi=150)
    plt.close()
