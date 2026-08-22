import pandas as pd
import os

def load_datasets(data_dir='data'):
    """Loads all three eBook datasets into pandas DataFrames."""
    path_a = os.path.join(data_dir, 'BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx')
    path_b = os.path.join(data_dir, 'BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx')
    path_c = os.path.join(data_dir, 'BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx')
    
    df_a = pd.read_excel(path_a, sheet_name='Booklist')
    df_b = pd.read_excel(path_b, sheet_name='Booklist')
    df_c = pd.read_excel(path_c, sheet_name='Booklist')
    
    return df_a, df_b, df_c

if __name__ == "__main__":
    df_a, df_b, df_c = load_datasets()
    print(f"Dataset A loaded: {df_a.shape}")
    print(f"Dataset B loaded: {df_b.shape}")
    print(f"Dataset C loaded: {df_c.shape}")