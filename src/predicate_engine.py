"""
predicate_engine.py
Crisp (Boolean) predicate querying over the three eBook datasets.

Each dataset exposes different fields, so each dataset gets its own
field-search configuration instead of forcing one schema on all three:

  Dataset A (Existing Collection) : searchable in Title only
                                     (no subject/discipline column exists)
  Dataset B (Academic Catalogue)  : searchable in Title + Discipline (L1-L2)
  Dataset C (Acquisition Catalog.): searchable in Title + Category + Discipline

A predicate query is simply:
    match(record) = TRUE  iff  any searchable field of record contains
                                any keyword in the keyword set (whole-word,
                                case-insensitive)

This is the crisp / predicate-only stage described in the assessment
(Section 3): it returns a binary satisfied / not-satisfied partition of the
dataset, with no notion of "how well" a record matches.
"""

import re
import pandas as pd

# Field configuration: which columns are queried for each dataset.
DATASET_FIELDS = {
    "A": ["Title"],
    "B": ["Title", "Discipline (Level 1)", "Discipline (Level 2)",
          "Discipline (Level 3)", "Discipline (Level 4)"],
    "C": ["Title", "Category", "Discipline"],
}


def _build_pattern(keywords):
    """Whole-word, case-insensitive OR pattern from a keyword list."""
    escaped = [r"\b" + re.escape(kw) + r"\b" for kw in keywords]
    return "|".join(escaped)


def predicate_query(df, dataset_key, keywords, extra_fields=None):
    """Runs a crisp predicate query over one dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataset to query (df_a, df_b, or df_c).
    dataset_key : {"A", "B", "C"}
        Determines which columns are searched.
    keywords : list[str]
        Subject / discipline / title terms that define the query condition.
    extra_fields : list[str], optional
        Additional columns to search beyond the dataset default (used when a
        scenario wants to widen or narrow the searchable fields).

    Returns
    -------
    pandas.DataFrame
        The subset of `df` satisfying the predicate (record.matches == True),
        with a boolean helper column '_matched_field' recording which column
        triggered the match (useful for the "why satisfied" explanation
        required in Section 7 of the report).
    """
    fields = list(DATASET_FIELDS.get(dataset_key, []))
    if extra_fields:
        fields += [f for f in extra_fields if f not in fields]
    fields = [f for f in fields if f in df.columns]

    if not fields:
        raise ValueError(f"No searchable fields found for dataset {dataset_key}")

    pattern = _build_pattern(keywords)
    mask = pd.Series(False, index=df.index)
    matched_field = pd.Series("", index=df.index)

    for col in fields:
        col_mask = df[col].astype(str).str.contains(pattern, case=False, regex=True, na=False)
        # record first field that matched, for explainability
        newly = col_mask & (~mask)
        matched_field.loc[newly] = col
        mask = mask | col_mask

    result = df[mask].copy()
    result["_matched_field"] = matched_field[mask]
    return result


def classify_relevance(title, direct_keywords, support_keywords_map):
    """Crisp classification of a record's relationship to the scenario topic.

    Returns one label from:
      "Directly Related"      - direct topic keyword found in title
      "Programming Support"   - a programming-support keyword found
      "Mathematical Support"  - a maths-support keyword found
      "Other Justified Match" - matched via discipline/category field only,
                                 no keyword found in the title itself

    support_keywords_map: dict like {"Programming Support": [...], "Mathematical Support": [...]}
    """
    title_low = str(title).lower()
    if any(kw.lower() in title_low for kw in direct_keywords):
        return "Directly Related"
    for label, kws in support_keywords_map.items():
        if any(kw.lower() in title_low for kw in kws):
            return label
    return "Other Justified Match"
