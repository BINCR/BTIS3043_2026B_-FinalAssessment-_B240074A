import math
import pandas as pd

from src.predicate_engine import combined_predicate_query
from src.fuzzy_engine import (
    format_membership,
    relevance_membership,
    recency_membership,
)


def _mini_df(titles):
    return pd.DataFrame({
        "Title": titles,
        "Copyright Year": [2024] * len(titles),
        "Unit Net Price": [100.0] * len(titles),
        "_source_order": range(1, len(titles) + 1),
    })


def test_security_false_positive_is_rejected():
    df = _mini_df(["Understanding Food Security", "Security in Computing"])
    result = combined_predicate_query(df, "A", "S2")
    assert "Understanding Food Security" not in set(result["Title"])
    assert "Security in Computing" in set(result["Title"])


def test_direct_and_related_security_are_distinguished():
    df = _mini_df(["Network Security", "Applied Cryptography"])
    result = combined_predicate_query(df, "A", "S2")
    labels = dict(zip(result["Title"], result["Relationship"]))
    assert labels["Network Security"] == "Direct Security"
    assert labels["Applied Cryptography"] == "Security-Related Support"


def test_adobe_reader_is_treated_as_suitable_digital_format():
    assert format_membership("Adobe Reader") == 0.85
    assert format_membership("ePub") == 1.00


def test_recency_membership_is_bounded_and_monotonic_for_examples():
    assert 0 <= recency_membership(2026) <= 1
    assert recency_membership(2026) >= recency_membership(2021)
    assert recency_membership(2021) >= recency_membership(2016)


def test_security_related_relevance_is_lower_than_direct():
    direct = relevance_membership("Direct Security", "Title", "S2")
    related = relevance_membership("Security-Related Support", "Title", "S2")
    assert direct > related
    assert math.isclose(direct, 1.0)
