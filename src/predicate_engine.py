"""
predicate_engine.py

Crisp (Boolean) predicate reasoning for the BTIS3043 eBook intelligent system.

Each dataset contains different fields, so dataset-specific search fields are
used instead of forcing all three datasets into one common structure:

Dataset A (Existing Collection):
    searchable in Title only.

Dataset B (Academic Catalogue):
    searchable in Title and Discipline (Level 1-4).

Dataset C (Acquisition Catalogue):
    searchable in Title, Category and Discipline.

The predicate stage uses Boolean reasoning to determine whether a record
satisfies the scenario conditions. A record either satisfies the predicate
or does not satisfy it.

Two predicate levels are implemented:

1. basic_predicate_query()
   Demonstrates a basic direct-topic predicate.

2. combined_predicate_query()
   Combines several meaningful Boolean relationship predicates to identify
   a broader and more suitable candidate set.

The combined predicate query is used as the main candidate-generation stage
before fuzzy evaluation. The fuzzy stage then evaluates the degree of
suitability of the predicate-matched records and supports final ranking.
"""

import re
import pandas as pd

from .data_loader import DATASET_SPECS
from .knowledge_base import (
    SECURITY_CONTEXT_TERMS,
    SECURITY_EXCLUSION_TERMS,
    get_scenario,
)


def _normalize_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _build_pattern(keyword):
    """Safe whole-token/phrase regex, including symbols such as C++."""
    keyword = str(keyword).strip()
    # Treat the C programming language as a standalone token without
    # accidentally turning C# or C++ into a match for plain C.
    if keyword.lower() == "c":
        return r"(?<![\w+#])c(?![\w+#])"
    return rf"(?<!\w){re.escape(keyword)}(?!\w)"


def _keyword_matches(text, keyword):
    text = _normalize_text(text)
    if not text:
        return False
    return bool(re.search(_build_pattern(keyword), text, flags=re.IGNORECASE))


def _valid_generic_security_context(text):
    """Reject generic non-computing uses of 'security'."""
    low = _normalize_text(text).lower()
    if "security" not in low:
        return False
    if any(term in low for term in SECURITY_EXCLUSION_TERMS):
        return False
    return any(term in low for term in SECURITY_CONTEXT_TERMS)


def _valid_keyword_match(text, keyword, scenario_id):
    keyword_low = str(keyword).strip().lower()
    if scenario_id == "S2" and keyword_low == "security":
        return _valid_generic_security_context(text)
    return _keyword_matches(text, keyword)


def _match_keywords_in_row(row, fields, keywords, scenario_id):
    matched_terms = []
    matched_fields = []

    for field in fields:
        text = row.get(field, "")
        if pd.isna(text):
            continue
        for keyword in keywords:
            if _valid_keyword_match(text, keyword, scenario_id):
                if keyword not in matched_terms:
                    matched_terms.append(keyword)
                if field not in matched_fields:
                    matched_fields.append(field)

    return matched_terms, matched_fields


def basic_predicate_query(df, dataset_key, scenario_id):
    """Basic predicate: return records matching the direct-topic group only."""
    dataset_key = str(dataset_key).upper()
    scenario_id = str(scenario_id).upper()
    scenario = get_scenario(scenario_id)
    fields = [
        f for f in DATASET_SPECS[dataset_key]["search_fields"] if f in df.columns
    ]
    direct_group = scenario["groups"][0]

    rows = []
    for index, row in df.iterrows():
        terms, matched_fields = _match_keywords_in_row(
            row, fields, direct_group["keywords"], scenario_id
        )
        if terms:
            record = row.copy()
            record["Relationship"] = direct_group["label"]
            record["Matched_Terms"] = ", ".join(terms)
            record["Matched_Fields"] = ", ".join(matched_fields)
            record["Predicate_Type"] = "Basic direct-topic predicate"
            record["Predicate_Expression"] = direct_group["label"]
            rows.append(record)

    if not rows:
        return pd.DataFrame(columns=list(df.columns) + [
            "Relationship", "Matched_Terms", "Matched_Fields",
            "Predicate_Type", "Predicate_Expression"
        ])
    return pd.DataFrame(rows).reset_index(drop=True)


def combined_predicate_query(df, dataset_key, scenario_id):
    """Run the rubric-aligned combined Boolean predicate query.

    Scenario 1: Direct_AI OR Programming_Support OR Mathematical_Support.
    Scenario 2: Direct_Security OR Security_Related_Support, with an extra
    computing-context guard when the generic keyword 'security' is the match.

    All matching groups are retained for explanation, while Relationship is
    assigned to the strongest (lowest-priority-number) group.
    """
    dataset_key = str(dataset_key).upper()
    scenario_id = str(scenario_id).upper()
    scenario = get_scenario(scenario_id)

    if dataset_key not in DATASET_SPECS:
        raise ValueError("dataset_key must be 'A', 'B', or 'C'.")

    fields = [
        f for f in DATASET_SPECS[dataset_key]["search_fields"] if f in df.columns
    ]
    if not fields:
        raise ValueError(f"No searchable fields found for Dataset {dataset_key}.")

    accepted = []
    for _, row in df.iterrows():
        group_hits = []
        all_terms = []
        all_fields = []

        for group in scenario["groups"]:
            terms, matched_fields = _match_keywords_in_row(
                row, fields, group["keywords"], scenario_id
            )
            if terms:
                group_hits.append(
                    {
                        "label": group["label"],
                        "priority": group["priority"],
                        "terms": terms,
                        "fields": matched_fields,
                    }
                )
                for term in terms:
                    if term not in all_terms:
                        all_terms.append(term)
                for field in matched_fields:
                    if field not in all_fields:
                        all_fields.append(field)

        if not group_hits:
            continue

        strongest = sorted(group_hits, key=lambda x: x["priority"])[0]
        record = row.copy()
        record["Relationship"] = strongest["label"]
        record["Matched_Groups"] = " | ".join(hit["label"] for hit in group_hits)
        record["Matched_Terms"] = ", ".join(all_terms)
        record["Matched_Fields"] = ", ".join(all_fields)
        record["Crisp_Priority"] = strongest["priority"]
        record["Predicate_Type"] = "Combined Boolean predicate"
        record["Predicate_Expression"] = scenario["predicate_expression"]
        accepted.append(record)

    if not accepted:
        extra_cols = [
            "Relationship", "Matched_Groups", "Matched_Terms", "Matched_Fields",
            "Crisp_Priority", "Predicate_Type", "Predicate_Expression",
            "Predicate_Rank"
        ]
        return pd.DataFrame(columns=list(df.columns) + extra_cols)

    result = pd.DataFrame(accepted)
    result = result.sort_values(
        ["Crisp_Priority", "_source_order"], kind="stable"
    ).reset_index(drop=True)
    result["Predicate_Rank"] = range(1, len(result) + 1)
    return result


def predicate_query(df, dataset_key, scenario_id):
    """Backward-friendly alias for the actual combined candidate query."""
    return combined_predicate_query(df, dataset_key, scenario_id)