import numpy as np
import pandas as pd

def compute_recency_score(year, current_year=2026):
    """Computes fuzzy recency score based on copyright year."""
    if pd.isna(year):
        return 0.5
    age = current_year - int(year)
    if age <= 2:
        return 1.0
    elif age <= 5:
        return 0.8
    elif age <= 10:
        return 0.5
    else:
        return 0.2

def compute_relevance_score(title, direct_keywords, support_keywords):
    """Computes fuzzy relevance score based on keyword matching depth."""
    title_lower = str(title).lower()
    direct_match = any(dk.lower() in title_lower for dk in direct_keywords)
    support_match = sum(1 for sk in support_keywords if sk.lower() in title_lower)
    
    if direct_match:
        return 1.0, "Directly Related"
    elif support_match > 0:
        score = min(0.4 + (0.2 * support_match), 0.8)
        return score, "Supporting Reference"
    else:
        return 0.1, "Peripheral"

def compute_affordability_score(price, max_price=300.0):
    """Computes fuzzy affordability score based on price."""
    if pd.isna(price) or price <= 0:
        return 0.5 # Neutral if no price
    if price <= 50:
        return 1.0
    elif price >= max_price:
        return 0.1
    else:
        return float(1.0 - (price / max_price))