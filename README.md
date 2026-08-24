# BTIS3043 Artificial Intelligence — Final Assessment (2026B)

## System Goal

This repository implements a small intelligent eBook search and evaluation system for the two fixed BTIS3043 scenarios. It deliberately separates **crisp predicate reasoning** from **fuzzy suitability evaluation** so the system decisions are explainable and reproducible.

The three datasets are processed separately because their structures and available evidence differ.

## Rubric-aligned design

- **Problem/data/knowledge representation:** dataset-specific field specifications and explicit scenario knowledge groups.
- **Predicate reasoning:** both a basic direct-topic predicate and a combined Boolean predicate are demonstrated.
- **Fuzzy reasoning:** topic relevance, publication recency, format suitability, and affordability use values in `[0,1]`.
- **Missing evidence:** unavailable fuzzy components are excluded rather than assigned an artificial neutral value; remaining weights are re-normalised.
- **Ranking:** predicate-only ordering is compared with fuzzy ranking using `Predicate_Rank`, `Fuzzy_Rank`, and `Rank_Change`.
- **Explainability:** each accepted record stores matched terms, matched fields, relationship class, component memberships, and a decision reason.
- **Cross-dataset evaluation:** the notebook reports dataset size, topic coverage, field structure, format evidence, price evidence, match counts and ranking changes.

## Fixed scenarios

1. **Artificial Intelligence, Programming and Mathematical Foundations**
   - Direct AI
   - Programming support
   - Mathematical support

2. **Cybersecurity and Secure Computing**
   - Direct security
   - Security-related support
   - A context guard prevents generic phrases such as *Food Security* from being misclassified as cybersecurity.

## Project structure

```text
BTIS3043_2026B_FinalAssessment_B240074A/
├── README.md
├── requirements.txt
├── analysis.ipynb
├── data/
│   ├── BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx
│   ├── BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx
│   └── BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── knowledge_base.py
│   ├── predicate_engine.py
│   ├── fuzzy_engine.py
│   └── evaluation.py
└── tests/
    └── test_system.py
```

## Reproduce the results

From the repository root:

```bash
python -m pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

Then choose **Run All**.

For a command-line reproducibility check:

```bash
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

Run the correctness tests with:

```bash
python -m pytest -q
```

## Important implementation choices

### Predicate stage

The final candidate set is generated with a **combined Boolean predicate**, not just one large undifferentiated keyword list. The system also runs a basic direct-topic predicate so the report can explicitly demonstrate both basic and combined predicates.

### Security direct vs related relevance

Direct cybersecurity concepts and related secure-computing concepts are represented separately. For example, *Network Security* is direct, while *Cryptography* and *Digital Forensics* are treated as strong related support rather than automatically receiving the same relevance membership.

### Fuzzy aggregation

Default weights are:

- relevance = `0.45`
- recency = `0.25`
- format suitability = `0.15`
- affordability = `0.15`

If a dataset lacks one component (for example, Dataset B has no comparable price), that component is omitted and the remaining weights are re-normalised.

### Affordability

Affordability is **catalogue-relative**, not an absolute claim that a price is universally cheap. The fuzzy membership uses the 25th and 90th percentiles of the selected comparable price field within that dataset. Dataset C uses **Single user / 1-Year**, matching the stated licence arrangement in the output.

## Notes for submission

The notebook contains the complete executable evidence. In the 12-page report, show only the most important result tables, selected decision explanations, and cross-dataset comparisons rather than reproducing the full source code.
