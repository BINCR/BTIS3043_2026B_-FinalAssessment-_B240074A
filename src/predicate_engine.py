import pandas as pd
import re

def predicate_filter_dataset_a(df, keywords):
    """Filters Dataset A based on title keywords and returns categorized matches."""
    pattern = '|'.join([r'\b' + re.escape(kw) + r'\b' for kw in keywords])
    matched = df[df['Title'].str.contains(pattern, case=False, na=False)].copy()
    return matched

def predicate_filter_dataset_b(df, keywords):
    """Filters Dataset B based on title or discipline fields."""
    pattern = '|'.join([r'\b' + re.escape(kw) + r'\b' for kw in keywords])
    text_mask = df['Title'].str.contains(pattern, case=False, na=False)
    disc_mask = df['Discipline (Level 1)'].str.contains(pattern, case=False, na=False) | \
                df['Discipline (Level 2)'].str.contains(pattern, case=False, na=False)
    matched = df[text_mask | disc_mask].copy()
    return matched

def predicate_filter_dataset_c(df, keywords):
    """Filters Dataset C based on title, category, or discipline fields."""
    pattern = '|'.join([r'\b' + re.escape(kw) + r'\b' for kw in keywords])
    text_mask = df['Title'].str.contains(pattern, case=False, na=False)
    cat_mask = df['Category'].str.contains(pattern, case=False, na=False) | \
               df['Discipline'].str.contains(pattern, case=False, na=False)
    matched = df[text_mask | cat_mask].copy()
    return matched