"""
predicate_engine.py

Crisp (Boolean) predicate querying over the three eBook datasets.

Each dataset exposes different fields, so each dataset gets its own
field-search configuration instead of forcing one schema on all three:

Dataset A (Existing Collection):
    searchable in Title only

Dataset B (Academic Catalogue):
    searchable in Title + Discipline (Level 1-4)

Dataset C (Acquisition Catalogue):
    searchable in Title + Category + Discipline

A predicate query returns records that satisfy at least one defined
keyword condition.

This is the crisp / predicate-only stage of the intelligent system.
A record either satisfies the predicate or does not satisfy it.

The fuzzy stage will later evaluate how suitable each matched record is.
"""

import re
import pandas as pd


# ---------------------------------------------------------
# 1. DATASET FIELD CONFIGURATION
# ---------------------------------------------------------

DATASET_FIELDS = {
    "A": [
        "Title"
    ],

    "B": [
        "Title",
        "Discipline (Level 1)",
        "Discipline (Level 2)",
        "Discipline (Level 3)",
        "Discipline (Level 4)"
    ],

    "C": [
        "Title",
        "Category",
        "Discipline"
    ]
}


# ---------------------------------------------------------
# 2. REGEX / KEYWORD MATCHING
# ---------------------------------------------------------

def _build_pattern(keyword):
    """
    Builds a safe case-insensitive regex pattern for one keyword.

    (?<!\\w) and (?!\\w) are used instead of \\b so that keywords
    containing symbols such as C++ can still be matched correctly.
    """

    return rf"(?<!\w){re.escape(str(keyword))}(?!\w)"


def _keyword_matches(text, keyword):
    """
    Returns True when one keyword occurs in the text.
    Matching is case-insensitive.
    """

    text = str(text)

    return bool(
        re.search(
            _build_pattern(keyword),
            text,
            flags=re.IGNORECASE
        )
    )


# ---------------------------------------------------------
# 3. SPECIAL SECURITY CONTEXT CHECK
# ---------------------------------------------------------

def _is_valid_security_context(text):
    """
    Prevents general uses of the word 'security' from being treated
    automatically as cybersecurity.

    Examples that should be accepted:
        Computer Security
        Network Security
        Information Security
        Cyber Security
        Software Security
        Security Engineering

    Examples that should normally be rejected:
        Food Security
        Energy Security
        Social Security
    """

    text = str(text).lower()

    if "security" not in text:
        return False

    security_context_terms = [
        "computer",
        "computing",
        "cyber",
        "network",
        "information",
        "data",
        "software",
        "system",
        "systems",
        "digital",
        "internet",
        "web",
        "cloud",
        "database",
        "technology",
        "technologies",
        "cryptography",
        "cryptographic",
        "privacy",
        "secure",
        "security engineering",
        "information assurance",
        "forensic",
        "forensics"
    ]

    return any(
        term in text
        for term in security_context_terms
    )


def _valid_keyword_match(text, keyword):
    """
    Applies normal keyword matching.

    The generic keyword 'security' receives an additional context check
    so that unrelated records such as Food Security are not returned.
    """

    keyword_low = str(keyword).strip().lower()

    if keyword_low == "security":
        return _is_valid_security_context(text)

    return _keyword_matches(text, keyword)


# ---------------------------------------------------------
# 4. MAIN PREDICATE QUERY
# ---------------------------------------------------------

def predicate_query(
    df,
    dataset_key,
    keywords,
    extra_fields=None
):
    """
    Runs a crisp predicate query over one dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset A, B or C.

    dataset_key : {"A", "B", "C"}
        Determines which columns are searched.

    keywords : list[str]
        Keywords representing the scenario query.

    extra_fields : list[str], optional
        Additional columns to search if required.

    Returns
    -------
    pandas.DataFrame

        Only records satisfying at least one predicate condition.

        Two explanation columns are also added:

        _matched_field
            The first field where a match was found.

        _matched_terms
            The keyword or keywords that caused the record to match.
    """

    dataset_key = str(dataset_key).upper()

    if dataset_key not in DATASET_FIELDS:
        raise ValueError(
            f"Unknown dataset key: {dataset_key}. "
            "Use 'A', 'B', or 'C'."
        )

    # Get normal searchable fields
    fields = list(DATASET_FIELDS[dataset_key])

    # Add optional extra fields
    if extra_fields:
        for field in extra_fields:
            if field not in fields:
                fields.append(field)

    # Only keep columns that actually exist
    fields = [
        field
        for field in fields
        if field in df.columns
    ]

    if not fields:
        raise ValueError(
            f"No searchable fields found for Dataset {dataset_key}."
        )

    # Store result information
    mask = pd.Series(
        False,
        index=df.index
    )

    matched_field = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    matched_terms = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    # -----------------------------------------------------
    # Search every record
    # -----------------------------------------------------

    for index, row in df.iterrows():

        record_matched_terms = []
        record_matched_fields = []

        for field in fields:

            text = row.get(field, "")

            if pd.isna(text):
                continue

            for keyword in keywords:

                if _valid_keyword_match(text, keyword):

                    keyword_text = str(keyword)

                    if keyword_text not in record_matched_terms:
                        record_matched_terms.append(
                            keyword_text
                        )

                    if field not in record_matched_fields:
                        record_matched_fields.append(
                            field
                        )

        # If at least one predicate matched
        if record_matched_terms:

            mask.loc[index] = True

            matched_terms.loc[index] = ", ".join(
                record_matched_terms
            )

            matched_field.loc[index] = ", ".join(
                record_matched_fields
            )

    # Keep only matching records
    result = df.loc[mask].copy()

    # Add explanation columns
    result["_matched_field"] = matched_field.loc[mask]

    result["_matched_terms"] = matched_terms.loc[mask]

    return result


# ---------------------------------------------------------
# 5. RELATIONSHIP CLASSIFICATION
# ---------------------------------------------------------

def classify_relevance(
    title,
    direct_keywords,
    support_keywords_map
):
    """
    Gives each record a crisp relationship label.

    Possible labels include:

        Directly Related
        Programming Support
        Mathematical Support
        Other Justified Match

    Parameters
    ----------
    title : str
        Book title.

    direct_keywords : list[str]
        Keywords directly related to the main scenario.

    support_keywords_map : dict
        Example:

        {
            "Programming Support": [...],
            "Mathematical Support": [...]
        }

    Returns
    -------
    str
        Relationship label.
    """

    title = str(title)

    # -----------------------------------------------------
    # Direct topic relationship
    # -----------------------------------------------------

    for keyword in direct_keywords:

        if _valid_keyword_match(
            title,
            keyword
        ):

            return "Directly Related"

    # -----------------------------------------------------
    # Supporting relationships
    # -----------------------------------------------------

    for label, keywords in support_keywords_map.items():

        for keyword in keywords:

            if _valid_keyword_match(
                title,
                keyword
            ):

                return label

    # -----------------------------------------------------
    # Match may have occurred through discipline/category
    # rather than title
    # -----------------------------------------------------

    return "Other Justified Match"