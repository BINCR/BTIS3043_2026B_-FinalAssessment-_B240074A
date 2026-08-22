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

import pandas as pd


# =========================================================
# 1. RELEVANCE MEMBERSHIP
# =========================================================

def relevance_membership(label):
    """
    Convert a relationship label into fuzzy topic relevance.

    Values are in the range [0, 1].
    """

    mapping = {
        "Directly Related": 1.00,
        "Programming Support": 0.70,
        "Mathematical Support": 0.70,
        "Other Justified Match": 0.45
    }

    return mapping.get(
        str(label),
        0.40
    )


# =========================================================
# 2. RECENCY MEMBERSHIP
# =========================================================

def recency_membership(year, current_year=2026):
    """
    Fuzzy membership for publication recency.

    Age <= 2 years:
        1.00

    Age 3-5 years:
        decreases gradually from 1.00 to 0.60

    Age 6-10 years:
        decreases gradually from 0.60 to 0.30

    More than 10 years old:
        0.20

    Missing or invalid year:
        None
    """

    if pd.isna(year):
        return None

    try:
        y = int(float(year))
    except (TypeError, ValueError):
        return None

    age = current_year - y

    # Future year / current year / very recent
    if age <= 2:
        return 1.00

    # Recent
    elif age <= 5:
        return 1.00 - (
            (age - 2) * (0.40 / 3)
        )

    # Relatively recent
    elif age <= 10:
        return 0.60 - (
            (age - 5) * (0.30 / 5)
        )

    # Older publication
    else:
        return 0.20


# =========================================================
# 3. FORMAT SUITABILITY MEMBERSHIP
# =========================================================

def format_membership(format_value):
    """
    Evaluate how suitable the available format is as an eBook.

    This fuzzy variable is mainly useful for Datasets B and C,
    where an eBook Format field is available.

    Higher membership:
        EPUB
        PDF
        HTML / online digital formats

    Moderate membership:
        mixed or less clearly specified digital formats

    Missing format:
        None
    """

    if pd.isna(format_value):
        return None

    text = str(format_value).strip().lower()

    if not text:
        return None

    # Highly suitable common eBook formats
    highly_suitable = [
        "epub",
        "pdf",
        "html",
        "online",
        "ebook",
        "e-book"
    ]

    # Acceptable but less clearly standardised formats
    moderately_suitable = [
        "digital",
        "electronic",
        "web",
        "xml"
    ]

    if any(
        term in text
        for term in highly_suitable
    ):
        return 1.00

    if any(
        term in text
        for term in moderately_suitable
    ):
        return 0.70

    # Format exists but suitability is uncertain
    return 0.50


# Which field contains digital-format evidence
FORMAT_FIELDS = {
    "B": "eBook Format",
    "C": "eBook Format"
}


def get_format_score(row, dataset_key):
    """
    Obtain format suitability for one record.

    Dataset A has no configured format field, so None is returned.
    """

    dataset_key = str(dataset_key).upper()

    field = FORMAT_FIELDS.get(dataset_key)

    if field is None:
        return None

    if field not in row.index:
        return None

    return format_membership(
        row.get(field)
    )


# =========================================================
# 4. AFFORDABILITY MEMBERSHIP
# =========================================================

def affordability_membership(
    price,
    low,
    high
):
    """
    Fuzzy membership for affordability.

    price <= low:
        1.00

    price >= high:
        0.10

    Between low and high:
        linearly decreases from 1.00 to 0.10.

    Invalid/missing price:
        None
    """

    if pd.isna(price):
        return None

    try:
        p = float(price)
    except (TypeError, ValueError):
        return None

    if p <= 0:
        return None

    if p <= low:
        return 1.00

    elif p >= high:
        return 0.10

    else:
        return 1.00 - (
            0.90 *
            (p - low) /
            (high - low)
        )


# =========================================================
# 5. AFFORDABILITY FIELD CONFIGURATION
# =========================================================

AFFORDABILITY_FIELDS = {
    "A": "Unit Net Price",

    # Representative licensing arrangement for Dataset C.
    # A single-user one-year licence is used because it provides
    # a consistent price field across records.
    "C": "Single user / 1-Year"
}


def derive_affordability_thresholds(
    df,
    field,
    low_q=0.25,
    high_q=0.90
):
    """
    Derive affordability thresholds from the price distribution
    of the dataset itself.

    low:
        25th percentile

    high:
        90th percentile

    This avoids using one fixed price range for datasets whose
    price structures are very different.
    """

    if field not in df.columns:
        raise ValueError(
            f"Price field '{field}' not found."
        )

    series = pd.to_numeric(
        df[field],
        errors="coerce"
    ).dropna()

    series = series[
        series > 0
    ]

    if series.empty:
        raise ValueError(
            f"No valid price values found in '{field}'."
        )

    low = float(
        series.quantile(low_q)
    )

    high = float(
        series.quantile(high_q)
    )

    # Prevent division by zero
    if high <= low:
        high = low + 1.0

    return {
        "field": field,
        "low": low,
        "high": high
    }


def build_affordability_thresholds(
    df_a,
    df_c
):
    """
    Build affordability threshold configuration for
    Dataset A and Dataset C.
    """

    return {
        "A": derive_affordability_thresholds(
            df_a,
            AFFORDABILITY_FIELDS["A"]
        ),

        "C": derive_affordability_thresholds(
            df_c,
            AFFORDABILITY_FIELDS["C"]
        )
    }


def get_affordability_score(
    row,
    dataset_key,
    thresholds
):
    """
    Calculate affordability membership for one record.

    Dataset B has no configured comparable price field,
    therefore None is returned.
    """

    dataset_key = str(dataset_key).upper()

    if dataset_key not in AFFORDABILITY_FIELDS:
        return None

    if dataset_key not in thresholds:
        return None

    config = thresholds[
        dataset_key
    ]

    field = config["field"]

    if field not in row.index:
        return None

    return affordability_membership(
        row.get(field),
        config["low"],
        config["high"]
    )


# =========================================================
# 6. DEFAULT FUZZY WEIGHTS
# =========================================================

DEFAULT_WEIGHTS = {
    "relevance": 0.45,
    "recency": 0.25,
    "format": 0.15,
    "affordability": 0.15
}


# =========================================================
# 7. FUZZY AGGREGATION
# =========================================================

def aggregate_fuzzy_score(
    components,
    weights=None
):
    """
    Combine available fuzzy membership values using a
    weighted average.

    Missing components are excluded.

    The weights of the remaining components are then
    re-normalised so their sum becomes 1.

    Example
    -------
    components = {
        "relevance": 1.0,
        "recency": 0.8,
        "format": 1.0,
        "affordability": None
    }

    Returns
    -------
    score : float

    used_weights : dict
        Actual normalised weights used.

    missing : list
        Fuzzy components for which no evidence existed.
    """

    if weights is None:
        weights = DEFAULT_WEIGHTS

    available = {
        key: value
        for key, value in components.items()
        if value is not None
    }

    missing = [
        key
        for key, value in components.items()
        if value is None
    ]

    if not available:
        return 0.0, {}, missing

    total_weight = sum(
        weights.get(key, 0)
        for key in available
    )

    if total_weight == 0:
        return 0.0, {}, missing

    used_weights = {
        key: weights.get(key, 0) / total_weight
        for key in available
    }

    score = sum(
        used_weights[key] *
        available[key]
        for key in available
    )

    return (
        round(score, 4),
        used_weights,
        missing
    )


# =========================================================
# 8. RECORD-LEVEL FUZZY EVALUATION
# =========================================================

def evaluate_record(
    row,
    dataset_key,
    relationship_label,
    year_field,
    affordability_thresholds=None,
    weights=None
):
    """
    Evaluate one predicate-matched record.

    Returns relevance, recency, format suitability,
    affordability and the final fuzzy score.
    """

    dataset_key = str(
        dataset_key
    ).upper()

    # ---------------------------------------------
    # Relevance
    # ---------------------------------------------

    relevance_score = relevance_membership(
        relationship_label
    )

    # ---------------------------------------------
    # Recency
    # ---------------------------------------------

    if year_field in row.index:
        recency_score = recency_membership(
            row.get(year_field)
        )
    else:
        recency_score = None

    # ---------------------------------------------
    # Format suitability
    # ---------------------------------------------

    format_score = get_format_score(
        row,
        dataset_key
    )

    # ---------------------------------------------
    # Affordability
    # ---------------------------------------------

    affordability_score = None

    if affordability_thresholds is not None:

        affordability_score = (
            get_affordability_score(
                row,
                dataset_key,
                affordability_thresholds
            )
        )

    # ---------------------------------------------
    # Aggregate
    # ---------------------------------------------

    components = {
        "relevance": relevance_score,
        "recency": recency_score,
        "format": format_score,
        "affordability": affordability_score
    }

    final_score, used_weights, missing = (
        aggregate_fuzzy_score(
            components,
            weights
        )
    )

    return {
        "Relevance_Score": (
            round(relevance_score, 4)
            if relevance_score is not None
            else None
        ),

        "Recency_Score": (
            round(recency_score, 4)
            if recency_score is not None
            else None
        ),

        "Format_Score": (
            round(format_score, 4)
            if format_score is not None
            else None
        ),

        "Affordability_Score": (
            round(affordability_score, 4)
            if affordability_score is not None
            else None
        ),

        "Fuzzy_Score": final_score,

        "Used_Weights": used_weights,

        "Missing_Evidence": missing
    }