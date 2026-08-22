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

import os
import pandas as pd


# ---------------------------------------------------------
# Required columns for basic validation
# ---------------------------------------------------------

REQUIRED_COLUMNS = {
    "A": [
        "Title",
        "Copyright Year",
        "Unit Net Price"
    ],

    "B": [
        "Title",
        "Copyright",
        "eBook Format",
        "Discipline (Level 1)"
    ],

    "C": [
        "Title",
        "Copyright Year",
        "eBook Format",
        "Category",
        "Discipline",
        "Single user / 1-Year"
    ]
}


def _clean_column_names(df):
    """
    Remove leading/trailing whitespace from column names.

    This is useful because some source datasets contain headers
    such as 'Print ISBN ' and 'Origin ' with trailing spaces.
    """

    df = df.copy()

    df.columns = [
        column.strip()
        if isinstance(column, str)
        else column
        for column in df.columns
    ]

    return df


def _validate_columns(df, dataset_key):
    """
    Check that important columns required by the intelligent
    search system exist in the dataset.
    """

    required = REQUIRED_COLUMNS[dataset_key]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Dataset {dataset_key} is missing required "
            f"column(s): {missing}"
        )


def load_datasets(data_dir="data"):
    """
    Load all three BTIS3043 eBook datasets.

    Parameters
    ----------
    data_dir : str
        Folder containing the three Excel dataset files.

    Returns
    -------
    tuple
        (df_a, df_b, df_c)
    """

    # -----------------------------------------------------
    # File paths
    # -----------------------------------------------------

    path_a = os.path.join(
        data_dir,
        "BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx"
    )

    path_b = os.path.join(
        data_dir,
        "BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx"
    )

    path_c = os.path.join(
        data_dir,
        "BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx"
    )

    # -----------------------------------------------------
    # Check files exist
    # -----------------------------------------------------

    for path in (path_a, path_b, path_c):

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"Expected dataset not found: {path}"
            )

    # -----------------------------------------------------
    # Load Excel files
    # -----------------------------------------------------

    df_a = pd.read_excel(
        path_a,
        sheet_name="Booklist"
    )

    df_b = pd.read_excel(
        path_b,
        sheet_name="Booklist"
    )

    df_c = pd.read_excel(
        path_c,
        sheet_name="Booklist"
    )

    # -----------------------------------------------------
    # Clean column names
    # -----------------------------------------------------

    df_a = _clean_column_names(df_a)
    df_b = _clean_column_names(df_b)
    df_c = _clean_column_names(df_c)

    # -----------------------------------------------------
    # Validate important columns
    # -----------------------------------------------------

    _validate_columns(df_a, "A")
    _validate_columns(df_b, "B")
    _validate_columns(df_c, "C")

    return df_a, df_b, df_c


# ---------------------------------------------------------
# Quick test when this file is run directly
# ---------------------------------------------------------

if __name__ == "__main__":

    a, b, c = load_datasets()

    print(
        f"Dataset A - Existing Collection: "
        f"{a.shape[0]} records, {a.shape[1]} columns"
    )

    print(
        f"Dataset B - Academic Catalogue: "
        f"{b.shape[0]} records, {b.shape[1]} columns"
    )

    print(
        f"Dataset C - Acquisition Catalogue: "
        f"{c.shape[0]} records, {c.shape[1]} columns"
    )

    print("\nAll datasets loaded successfully.")