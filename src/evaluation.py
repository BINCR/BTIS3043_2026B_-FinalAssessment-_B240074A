"""Scenario execution and cross-dataset evaluation helpers."""

import pandas as pd

from .data_loader import DATASET_SPECS
from .predicate_engine import basic_predicate_query, combined_predicate_query
from .fuzzy_engine import apply_fuzzy_evaluation
from .knowledge_base import get_scenario


def run_scenario(datasets, scenario_id):
    """Run basic predicate, combined predicate and fuzzy ranking for A/B/C."""
    outputs = {}
    for key in ("A", "B", "C"):
        basic = basic_predicate_query(datasets[key], key, scenario_id)
        predicate = combined_predicate_query(datasets[key], key, scenario_id)
        fuzzy, thresholds = apply_fuzzy_evaluation(
            predicate, datasets[key], key, scenario_id
        )
        outputs[key] = {
            "basic": basic,
            "predicate": predicate,
            "fuzzy": fuzzy,
            "affordability_thresholds": thresholds,
        }
    return outputs


def comparison_summary(datasets, outputs, scenario_id):
    """Build a compact table for predicate-fuzzy and cross-dataset evaluation."""
    scenario = get_scenario(scenario_id)
    rows = []
    for key in ("A", "B", "C"):
        spec = DATASET_SPECS[key]
        basic = outputs[key]["basic"]
        pred = outputs[key]["predicate"]
        fuzzy = outputs[key]["fuzzy"]

        rows.append(
            {
                "Scenario": scenario_id,
                "Dataset": key,
                "Dataset size": len(datasets[key]),
                "Basic direct matches": len(basic),
                "Combined predicate matches": len(pred),
                "Match rate %": round((len(pred) / len(datasets[key]) * 100), 2)
                if len(datasets[key]) else 0.0,
                "Top fuzzy score": round(float(fuzzy["Fuzzy_Score"].max()), 4)
                if not fuzzy.empty else None,
                "Top relationship": fuzzy.iloc[0]["Relationship"]
                if not fuzzy.empty else "No match",
                "Search structure": spec["discipline_detail"],
                "Format evidence": "Yes" if spec["format_field"] else "No",
                "Price evidence": "Yes" if spec["price_field"] else "No",
                "Fuzzy ranking changed order": bool(
                    not fuzzy.empty and (fuzzy["Rank_Change"] != 0).any()
                ),
            }
        )
    return pd.DataFrame(rows)


def top_results(fuzzy_df, limit):
    """Select concise output columns while preserving rubric evidence."""
    if fuzzy_df.empty:
        return fuzzy_df
    cols = [
        "Fuzzy_Rank",
        "Predicate_Rank",
        "Rank_Change",
        "Title",
        "Relationship",
        "Matched_Terms",
        "Matched_Fields",
        "Relevance_Score",
        "Recency_Score",
        "Format_Score",
        "Affordability_Score",
        "Fuzzy_Score",
        "Decision_Reason",
    ]
    cols = [c for c in cols if c in fuzzy_df.columns]
    return fuzzy_df.loc[:, cols].head(limit)


def rerank_with_weights(fuzzy_df, weights, rank_name="Alternative_Rank"):
    """Re-rank existing fuzzy memberships under another weight set.

    This is used for a small sensitivity check. It does not change the main
    system output; it shows whether conclusions depend heavily on one set of
    weights.
    """
    if fuzzy_df.empty:
        return fuzzy_df.copy()

    component_columns = {
        "relevance": "Relevance_Score",
        "recency": "Recency_Score",
        "format": "Format_Score",
        "affordability": "Affordability_Score",
    }
    result = fuzzy_df.copy()
    alt_scores = []

    for _, row in result.iterrows():
        available = {
            name: row[col]
            for name, col in component_columns.items()
            if name in weights and not pd.isna(row[col])
        }
        denominator = sum(weights[name] for name in available)
        score = (
            sum(weights[name] * value for name, value in available.items())
            / denominator
            if denominator else float("nan")
        )
        alt_scores.append(score)

    result["Alternative_Score"] = alt_scores
    result = result.sort_values(
        ["Alternative_Score", "Relevance_Score", "Predicate_Rank"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)
    result[rank_name] = range(1, len(result) + 1)
    return result


def sensitivity_summary(fuzzy_df, alternative_weights, top_n=10):
    """Compare baseline fuzzy ranks with one alternative weighting scheme."""
    if fuzzy_df.empty:
        return pd.DataFrame()
    alt = rerank_with_weights(fuzzy_df, alternative_weights)
    merge_key = "_source_order" if "_source_order" in fuzzy_df.columns else "Title"
    left_cols = [merge_key, "Title", "Fuzzy_Rank", "Fuzzy_Score"]
    right_cols = [merge_key, "Alternative_Rank", "Alternative_Score"]
    merged = fuzzy_df[left_cols].merge(
        alt[right_cols],
        on=merge_key,
        how="outer",
    )
    merged["Sensitivity_Rank_Change"] = (
        merged["Fuzzy_Rank"] - merged["Alternative_Rank"]
    )
    return merged.sort_values("Fuzzy_Rank", kind="stable").head(top_n)
