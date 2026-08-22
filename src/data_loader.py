"""
data_loader.py
Loads the three eBook datasets used by the BTIS3043 Final Assessment.

Dataset A: Existing eBook Collection   -> the DCS department's CURRENT holdings
Dataset B: Academic eBook Catalogue    -> large vendor catalogue (candidate acquisitions)
Dataset C: eBook Acquisition Catalogue -> licensing catalogue (candidate acquisitions,
                                          priced under several concurrent-user/term plans)
"""

import os
import pandas as pd


def load_datasets(data_dir="data"):
    """Loads all three eBook datasets into pandas DataFrames.

    Returns
    -------
    (df_a, df_b, df_c) : tuple of pandas.DataFrame
    """
    path_a = os.path.join(data_dir, "BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx")
    path_b = os.path.join(data_dir, "BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx")
    path_c = os.path.join(data_dir, "BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx")

    for p in (path_a, path_b, path_c):
        if not os.path.exists(p):
            raise FileNotFoundError(f"Expected dataset not found: {p}")

    df_a = pd.read_excel(path_a, sheet_name="Booklist")
    df_b = pd.read_excel(path_b, sheet_name="Booklist")
    df_c = pd.read_excel(path_c, sheet_name="Booklist")

    # Light, non-destructive cleanup: strip whitespace from column names
    # (Dataset B/C have trailing spaces in some headers, e.g. "Print ISBN ")
    for df in (df_a, df_b, df_c):
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    return df_a, df_b, df_c


if __name__ == "__main__":
    a, b, c = load_datasets()
    print(f"Dataset A (Existing/Current Subscription): {a.shape} -> {list(a.columns)}")
    print(f"Dataset B (Academic Catalogue):             {b.shape} -> {list(b.columns)}")
    print(f"Dataset C (Acquisition/Licensing Catalogue): {c.shape} -> {list(c.columns)}")
