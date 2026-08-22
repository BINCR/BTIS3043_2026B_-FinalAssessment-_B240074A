"""
fuzzy_engine.py
Fuzzy reasoning layer applied AFTER predicate filtering.

Three fuzzy variables are defined. Each is scored on a continuous [0, 1]
membership scale rather than a crisp yes/no:

  1. Topic relevance   - how strongly the record's evidence supports the
                          scenario topic (direct vs. supporting vs. weak match)
  2. Recency           - how recent the copyright/publication year is
  3. Affordability      - how affordable the record is, WHERE price evidence
                          exists for that dataset

Not every dataset supplies every kind of evidence:
  - Dataset A (Existing Collection)   HAS a price field ('Unit Net Price')
                                       but NOT a discipline/subject field.
  - Dataset B (Academic Catalogue)    HAS a rich discipline hierarchy but
                                       NO price field at all.
  - Dataset C (Acquisition Catalogue) HAS both a discipline/category field
                                       AND price fields (a base list price
                                       plus 18 concurrent-user/term license
                                       prices). We use the "Single user /
                                       1-Year" plan as the representative
                                       acquisition price, since it is the
                                       smallest, most comparable committment
                                       across records.

Where evidence for a fuzzy variable is MISSING for a given dataset, that
variable is dropped from the aggregation (not defaulted to a fake neutral
score) and the remaining weights are re-normalised. This is deliberate: it
is the mechanism the report uses to discuss how "available evidence"
changes the outcome (see Section 7 of the assessment brief).
"""

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Relevance membership
# ---------------------------------------------------------------------------
def relevance_membership(label):
    """Maps a crisp relevance label (see predicate_engine.classify_relevance)
    to a fuzzy relevance-strength membership degree in [0, 1]."""
    mapping = {
        "Directly Related": 1.0,
        "Programming Support": 0.7,
        "Mathematical Support": 0.7,
        "Other Justified Match": 0.45,
    }
    return mapping.get(label, 0.4)


# ---------------------------------------------------------------------------
# 2. Recency membership (piecewise-linear / trapezoidal)
# ---------------------------------------------------------------------------
def recency_membership(year, current_year=2026):
    """Fuzzy 'recent' membership based on age = current_year - year.

        age <= 2   : 1.00  (Very Recent)
        2  < a <= 5: linear 1.00 -> 0.60  (Recent)
        5  < a <=10: linear 0.60 -> 0.30  (Relatively Recent)
        a > 10     : 0.20               (Dated)

    Returns None if year evidence is missing/unparseable, so the caller can
    exclude this variable rather than silently guessing.
    """
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None
    if pd.isna(year):
        return None

    age = current_year - y
    if age <= 2:
        return 1.0
    elif age <= 5:
        # linear interpolation 1.00 -> 0.60 across (2,5]
        return 1.0 - (age - 2) * (0.40 / 3)
    elif age <= 10:
        return 0.60 - (age - 5) * (0.30 / 5)
    else:
        return 0.20


# ---------------------------------------------------------------------------
# 3. Affordability membership (dataset-specific price scale)
# ---------------------------------------------------------------------------
def affordability_membership(price, low, high):
    """Fuzzy 'affordable' membership.

        price <= low  : 1.0
        price >= high : 0.1
        low < price < high : linear interpolation

    `low`/`high` are dataset-specific because Dataset A's per-unit textbook
    prices and Dataset C's per-seat licence prices live on very different
    scales. Returns None if price evidence is missing.
    """
    try:
        p = float(price)
    except (TypeError, ValueError):
        return None
    if pd.isna(price) or p <= 0:
        return None

    if p <= low:
        return 1.0
    elif p >= high:
        return 0.1
    else:
        return 1.0 - 0.9 * (p - low) / (high - low)


# Which price field represents "affordability" evidence for each dataset.
# Dataset B has NO price field at all -> intentionally absent from this dict,
# so affordability is dropped (not faked) for every Dataset B record.
AFFORDABILITY_FIELDS = {
    "A": "Unit Net Price",
    "C": "Single user / 1-Year",   # smallest, most comparable license tier
}


def derive_affordability_thresholds(df, field, low_q=0.25, high_q=0.90):
    """Derives dataset-specific (low, high) affordability thresholds from
    that dataset's OWN price distribution (25th / 90th percentile by
    default), rather than hard-coding a fixed price band that would not
    transfer sensibly between a per-unit textbook price (Dataset A) and a
    per-seat annual licence price (Dataset C)."""
    series = df[field].dropna()
    low = float(series.quantile(low_q))
    high = float(series.quantile(high_q))
    return {"field": field, "low": low, "high": high}


def build_affordability_thresholds(df_a, df_c):
    """Convenience wrapper producing the AFFORDABILITY_THRESHOLDS dict for
    Datasets A and C from the datasets actually supplied at runtime."""
    return {
        "A": derive_affordability_thresholds(df_a, AFFORDABILITY_FIELDS["A"]),
        "C": derive_affordability_thresholds(df_c, AFFORDABILITY_FIELDS["C"]),
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS = {"relevance": 0.5, "recency": 0.3, "affordability": 0.2}


def aggregate_fuzzy_score(components, weights=None):
    """Weighted-average aggregation over whichever fuzzy components are
    actually available (not None), re-normalising weights over the
    available subset. This makes the 'missing evidence' case explicit and
    auditable instead of quietly injecting a neutral filler value.

    Parameters
    ----------
    components : dict[str, float or None]
        e.g. {"relevance": 0.9, "recency": 0.6, "affordability": None}
    weights : dict[str, float], optional

    Returns
    -------
    (score, used_weights, missing) : tuple
        score          - the aggregated fuzzy suitability score in [0, 1]
        used_weights   - the re-normalised weights actually applied
        missing        - list of component names that were unavailable
    """
    weights = weights or DEFAULT_WEIGHTS
    available = {k: v for k, v in components.items() if v is not None}
    missing = [k for k in components if k not in available]

    if not available:
        return 0.0, {}, missing

    total_w = sum(weights[k] for k in available)
    used_weights = {k: weights[k] / total_w for k in available}
    score = sum(used_weights[k] * available[k] for k in available)
    return round(score, 4), used_weights, missing
