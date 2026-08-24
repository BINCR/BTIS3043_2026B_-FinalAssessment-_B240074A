"""
data_loader.py

Loads the three eBook datasets used by the BTIS3043 Final Assessment.

Dataset A:
    Existing eBook Collection
    -> DCS department's current holdings

Dataset B:
    Academic eBook Catalogue
    -> Large academic/vendor catalogue

Dataset C:
    eBook Acquisition Catalogue
    -> Candidate acquisitions with licensing and pricing options
"""

from pathlib import Path
import pandas as pd


DATASET_SPECS = {
    "A": {
        "name": "Existing eBook Collection",
        "filename": "BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx",
        "search_fields": ["Title"],
        "year_field": "Copyright Year",
        "format_field": None,
        "price_field": "Unit Net Price",
        "discipline_detail": "None; title only",
        "collection_role": "Current/existing collection",
        "required": ["Title", "Copyright Year", "Unit Net Price"],
    },
    "B": {
        "name": "Academic eBook Catalogue",
        "filename": "BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx",
        "search_fields": [
            "Title",
            "Discipline (Level 1)",
            "Discipline (Level 2)",
            "Discipline (Level 3)",
            "Discipline (Level 4)",
        ],
        "year_field": "Copyright",
        "format_field": "eBook Format",
        "price_field": None,
        "discipline_detail": "Four discipline levels",
        "collection_role": "Academic/vendor catalogue",
        "required": [
            "Title",
            "Copyright",
            "eBook Format",
            "Discipline (Level 1)",
            "Discipline (Level 2)",
            "Discipline (Level 3)",
            "Discipline (Level 4)",
        ],
    },
    "C": {
        "name": "eBook Acquisition Catalogue",
        "filename": "BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx",
        "search_fields": ["Title", "Category", "Discipline"],
        "year_field": "Copyright Year",
        "format_field": "eBook Format",
        "price_field": "Single user / 1-Year",
        "discipline_detail": "Category + discipline",
        "collection_role": "Potential acquisition catalogue",
        "required": [
            "Title",
            "Copyright Year",
            "eBook Format",
            "Category",
            "Discipline",
            "Single user / 1-Year",
        ],
    },
}


def _clean_column_names(df):
    cleaned = df.copy()
    cleaned.columns = [
        c.strip() if isinstance(c, str) else c for c in cleaned.columns
    ]
    return cleaned


def _validate_columns(df, dataset_key):
    required = DATASET_SPECS[dataset_key]["required"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset {dataset_key} is missing required column(s): {missing}"
        )


def _coerce_core_numeric_fields(df, dataset_key):
    result = df.copy()
    spec = DATASET_SPECS[dataset_key]
    year_field = spec["year_field"]
    price_field = spec["price_field"]

    result[year_field] = pd.to_numeric(result[year_field], errors="coerce")
    if price_field:
        result[price_field] = pd.to_numeric(result[price_field], errors="coerce")
    return result


def load_dataset(dataset_key, data_dir="data"):
    """Load one dataset by key (A, B or C)."""
    dataset_key = str(dataset_key).upper()
    if dataset_key not in DATASET_SPECS:
        raise ValueError("dataset_key must be 'A', 'B', or 'C'.")

    path = Path(data_dir) / DATASET_SPECS[dataset_key]["filename"]
    if not path.exists():
        raise FileNotFoundError(f"Expected dataset not found: {path}")

    df = pd.read_excel(path, sheet_name="Booklist")
    df = _clean_column_names(df)
    _validate_columns(df, dataset_key)
    df = _coerce_core_numeric_fields(df, dataset_key)

    # Stable source-order ID is useful when comparing predicate-only ordering
    # with fuzzy ranking.
    df = df.copy()
    df["_source_order"] = range(1, len(df) + 1)
    return df


def load_datasets(data_dir="data"):
    """Load all three datasets and return a dict keyed by A, B and C."""
    return {
        key: load_dataset(key, data_dir=data_dir)
        for key in ("A", "B", "C")
    }


def dataset_profile(datasets):
    """Return a compact evidence/structure profile for cross-dataset analysis."""
    rows = []
    for key in ("A", "B", "C"):
        df = datasets[key]
        spec = DATASET_SPECS[key]
        rows.append(
            {
                "Dataset": key,
                "Role": spec["collection_role"],
                "Records": len(df),
                "Search fields": ", ".join(spec["search_fields"]),
                "Discipline detail": spec["discipline_detail"],
                "Year evidence": "Yes" if spec["year_field"] else "No",
                "Format evidence": "Yes" if spec["format_field"] else "No",
                "Comparable price": "Yes" if spec["price_field"] else "No",
                "Selected price field": spec["price_field"] or "Not available",
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data = load_datasets()
    print(dataset_profile(data).to_string(index=False))
