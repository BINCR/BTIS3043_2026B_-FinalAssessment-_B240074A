# BTIS3043 Artificial Intelligence — Final Assessment (2026B)

## Project Overview

This project develops a small intelligent eBook search and evaluation system for the BTIS3043 Artificial Intelligence Final Assessment.

The system searches and evaluates academic reference eBooks using three provided datasets:

- **Dataset A — Existing eBook Collection**
- **Dataset B — Academic eBook Catalogue**
- **Dataset C — eBook Acquisition Catalogue**

The system combines:

- predicate-based reasoning;
- fuzzy reasoning;
- result ranking; and
- comparison between predicate-only and fuzzy-enhanced results.

Two fixed scenarios are implemented:

1. **Artificial Intelligence, Programming and Mathematical Foundations**
2. **Cybersecurity and Secure Computing**

---

## Project Structure

```text
BTIS3043_2026B_-FinalAssessment-_B240074A/
│
├── README.md
├── requirements.txt
├── .gitignore
├── analysis.ipynb
│
├── src/
│   ├── data_loader.py
│   ├── predicate_engine.py
│   └── fuzzy_engine.py
│
└── data/
    ├── BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx
    ├── BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx
    └── BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx