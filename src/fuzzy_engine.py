"""
fuzzy_engine.py

Fuzzy reasoning layer applied AFTER predicate filtering.

Four fuzzy variables are considered:

1. Topic relevance
   - How strongly the record supports the scenario topic.

2. Recency
   - How recent the publication/copyright year is.

3. Format suitability
   - How suitable the available digital/eBook format is.

4. Affordability
   - How affordable the record is where comparable price evidence exists.

Not every dataset provides every type of evidence.

Dataset A:
    - Has price information.
    - Does not provide a useful eBook-format field.

Dataset B:
    - Has discipline information.
    - Has eBook Format.
    - Does not have comparable price information.

Dataset C:
    - Has discipline/category information.
    - Has eBook Format.
    - Has licensing price information.

When a fuzzy component is unavailable, it is NOT replaced by an
artificial neutral score. Instead, that component is excluded and
the remaining weights are re-normalised.

This allows the system to reflect differences in available evidence
between the three datasets.
"""

import math
import pandas as pd

from .data_loader import DATASET_SPECS
from .knowledge_base import get_scenario


def _clip01(value):
    return max(0.0, min(1.0, float(value)))


def relevance_membership(relationship, matched_fields, scenario_id):
    """Fuzzy membership in the set 'highly topic-relevant'.

    Relationship strength supplies the base membership. A title match is
    stronger evidence than a metadata-only match, while evidence appearing in
    multiple fields gives a small confidence increase.
    """
    scenario = get_scenario(scenario_id)
    base_by_label = {
        group["label"]: group["base_relevance"] for group in scenario["groups"]
    }
    score = base_by_label.get(str(relationship), 0.45)

    fields = [f.strip() for f in str(matched_fields).split(",") if f.strip()]
    if fields and "Title" not in fields:
        score -= 0.08
    if len(fields) >= 2:
        score += 0.03
    return round(_clip01(score), 4)


def recency_membership(year, current_year=2026):
    """Piecewise-linear membership in the fuzzy set 'recent'."""
    if pd.isna(year):
        return math.nan
    try:
        age = max(0.0, float(current_year) - float(year))
    except (TypeError, ValueError):
        return math.nan

    if age <= 2:
        score = 1.00
    elif age <= 5:
        # 1.00 at 2 years -> 0.70 at 5 years
        score = 1.00 - ((age - 2) / 3) * 0.30
    elif age <= 10:
        # 0.70 at 5 years -> 0.30 at 10 years
        score = 0.70 - ((age - 5) / 5) * 0.40
    elif age <= 15:
        # 0.30 at 10 years -> 0.10 at 15 years
        score = 0.30 - ((age - 10) / 5) * 0.20
    else:
        score = 0.10
    return round(_clip01(score), 4)


def format_membership(value):
    """Membership in the fuzzy set 'suitable eBook format'."""
    if pd.isna(value) or not str(value).strip():
        return math.nan
    text = str(value).strip().lower()

    if "epub" in text or "pdf" in text:
        return 1.00
    if "html" in text or "web" in text:
        return 0.90
    if "ebook" in text or "e-book" in text:
        return 0.90
    if "adobe reader" in text or "adobe digital" in text:
        return 0.85
    if "digital" in text or "electronic" in text:
        return 0.75
    return 0.50


def affordability_thresholds(full_df, price_field):
    """Return catalogue-relative low/high price anchors (Q25, Q90)."""
    if not price_field or price_field not in full_df.columns:
        return None
    prices = pd.to_numeric(full_df[price_field], errors="coerce").dropna()
    prices = prices[prices >= 0]
    if prices.empty:
        return None
    q25 = float(prices.quantile(0.25))
    q90 = float(prices.quantile(0.90))
    if q90 <= q25:
        q90 = q25 + 1e-9
    return {"low": q25, "high": q90}


def affordability_membership(price, thresholds):
    """Membership in 'affordable' using data-driven catalogue anchors."""
    if thresholds is None or pd.isna(price):
        return math.nan
    try:
        price = float(price)
    except (TypeError, ValueError):
        return math.nan

    low = thresholds["low"]
    high = thresholds["high"]
    if price <= low:
        return 1.00
    if price >= high:
        return 0.00
    score = 1.00 - ((price - low) / (high - low))
    return round(_clip01(score), 4)


def _membership_label(score):
    if pd.isna(score):
        return "Unavailable"
    if score >= 0.80:
        return "High"
    if score >= 0.50:
        return "Moderate"
    return "Low"


def _weighted_score(components, weights):
    available = {
        name: value
        for name, value in components.items()
        if not pd.isna(value)
    }
    if not available:
        return math.nan, 0.0, {}

    denominator = sum(weights[name] for name in available)
    contributions = {
        name: weights[name] * available[name] for name in available
    }
    score = sum(contributions.values()) / denominator
    normalised_contributions = {
        name: value / denominator for name, value in contributions.items()
    }
    return round(_clip01(score), 4), round(denominator, 4), normalised_contributions


def _decision_reason(row, contributions):
    if not contributions:
        return "No fuzzy evidence was available."

    strongest = max(contributions, key=contributions.get)
    labels = {
        "relevance": "topic relevance",
        "recency": "recency",
        "format": "format suitability",
        "affordability": "affordability",
    }
    unavailable = []
    for component, col in {
        "recency": "Recency_Score",
        "format": "Format_Score",
        "affordability": "Affordability_Score",
    }.items():
        if pd.isna(row.get(col)):
            unavailable.append(labels[component])

    reason = f"Main positive driver: {labels[strongest]}."
    if unavailable:
        reason += " Unavailable evidence excluded and weights re-normalised: " + ", ".join(unavailable) + "."
    return reason


def apply_fuzzy_evaluation(predicate_results, full_df, dataset_key, scenario_id):
    """Calculate fuzzy memberships, aggregate suitability, and rank results."""
    dataset_key = str(dataset_key).upper()
    scenario_id = str(scenario_id).upper()
    scenario = get_scenario(scenario_id)
    spec = DATASET_SPECS[dataset_key]

    if predicate_results.empty:
        return predicate_results.copy(), None

    result = predicate_results.copy()
    year_field = spec["year_field"]
    format_field = spec["format_field"]
    price_field = spec["price_field"]
    thresholds = affordability_thresholds(full_df, price_field)

    result["Relevance_Score"] = result.apply(
        lambda r: relevance_membership(
            r["Relationship"], r["Matched_Fields"], scenario_id
        ), axis=1
    )
    result["Recency_Score"] = result[year_field].apply(recency_membership)

    if format_field:
        result["Format_Score"] = result[format_field].apply(format_membership)
    else:
        result["Format_Score"] = math.nan

    if price_field:
        result["Affordability_Score"] = result[price_field].apply(
            lambda x: affordability_membership(x, thresholds)
        )
    else:
        result["Affordability_Score"] = math.nan

    fuzzy_scores = []
    denominators = []
    reasons = []
    available_evidence = []

    for _, row in result.iterrows():
        components = {
            "relevance": row["Relevance_Score"],
            "recency": row["Recency_Score"],
            "format": row["Format_Score"],
            "affordability": row["Affordability_Score"],
        }
        score, denominator, contributions = _weighted_score(
            components, scenario["weights"]
        )
        fuzzy_scores.append(score)
        denominators.append(denominator)
        available_evidence.append(
            ", ".join(name for name, value in components.items() if not pd.isna(value))
        )
        reasons.append(_decision_reason(row, contributions))

    result["Relevance_Level"] = result["Relevance_Score"].apply(_membership_label)
    result["Recency_Level"] = result["Recency_Score"].apply(_membership_label)
    result["Format_Level"] = result["Format_Score"].apply(_membership_label)
    result["Affordability_Level"] = result["Affordability_Score"].apply(_membership_label)
    result["Available_Fuzzy_Evidence"] = available_evidence
    result["Effective_Weight_Total"] = denominators
    result["Fuzzy_Score"] = fuzzy_scores
    result["Decision_Reason"] = reasons

    result = result.sort_values(
        ["Fuzzy_Score", "Relevance_Score", "Recency_Score", "Predicate_Rank"],
        ascending=[False, False, False, True],
        kind="stable",
    ).reset_index(drop=True)
    result["Fuzzy_Rank"] = range(1, len(result) + 1)
    result["Rank_Change"] = result["Predicate_Rank"] - result["Fuzzy_Rank"]
    return result, thresholds


def explain_record(row, dataset_key):
    """Return a concise, human-readable decision explanation."""
    spec = DATASET_SPECS[dataset_key]
    pieces = [
        f"Relationship={row['Relationship']}",
        f"matched terms={row['Matched_Terms']}",
        f"matched fields={row['Matched_Fields']}",
        f"relevance={row['Relevance_Score']:.2f}",
        f"recency={row['Recency_Score']:.2f}" if not pd.isna(row['Recency_Score']) else "recency=NA",
        f"format={row['Format_Score']:.2f}" if not pd.isna(row['Format_Score']) else "format=NA",
        f"affordability={row['Affordability_Score']:.2f}" if not pd.isna(row['Affordability_Score']) else "affordability=NA",
        f"final={row['Fuzzy_Score']:.4f}",
    ]
    if spec["price_field"]:
        pieces.append(f"price field={spec['price_field']}")
    pieces.append(row["Decision_Reason"])
    return "; ".join(pieces)
