"""Knowledge representation for the two fixed BTIS3043 scenarios.

The scenario dictionaries keep crisp relationship classes separate from
fuzzy preference weights. This makes the implementation easy to explain in
the report: predicates decide whether a record belongs to the candidate set,
while fuzzy reasoning decides how suitable each candidate is.
"""

SCENARIOS = {
    "S1": {
        "name": "Artificial Intelligence, Programming and Mathematical Foundations",
        "predicate_expression": (
            "Direct_AI OR Programming_Support OR Mathematical_Support"
        ),
        "groups": [
            {
                "label": "Direct AI",
                "priority": 1,
                "base_relevance": 1.00,
                "keywords": [
                    "artificial intelligence",
                    "intelligent systems",
                    "intelligent system",
                    "machine learning",
                    "computer vision",
                    "robotics",
                    "robot",
                    "robots",
                    "expert systems",
                    "expert system",
                    "knowledge representation",
                    "deep learning",
                    "neural networks",
                    "neural network",
                ],
            },
            {
                "label": "Programming Support",
                "priority": 2,
                "base_relevance": 0.78,
                "keywords": [
                    "python",
                    "java",
                    "c++",
                    "c programming",
                    "c",
                    "programming",
                    "algorithm",
                    "algorithms",
                    "data structure",
                    "data structures",
                ],
            },
            {
                "label": "Mathematical Support",
                "priority": 2,
                "base_relevance": 0.72,
                "keywords": [
                    "statistics",
                    "statistical",
                    "probability",
                    "linear algebra",
                    "discrete mathematics",
                    "calculus",
                    "optimization",
                    "optimisation",
                    "decision analysis",
                ],
            },
        ],
        "weights": {
            "relevance": 0.45,
            "recency": 0.25,
            "format": 0.15,
            "affordability": 0.15,
        },
    },
    "S2": {
        "name": "Cybersecurity and Secure Computing",
        "predicate_expression": (
            "Direct_Security OR Security_Related_Support, with a computing-context "
            "guard for the generic word 'security'"
        ),
        "groups": [
            {
                "label": "Direct Security",
                "priority": 1,
                "base_relevance": 1.00,
                "keywords": [
                    "cybersecurity",
                    "cyber security",
                    "computer security",
                    "security in computing",
                    "network security",
                    "information security",
                    "secure computing",
                    "secure systems",
                    "secure system",
                    "software security",
                    "information assurance",
                    "security",
                ],
            },
            {
                "label": "Security-Related Support",
                "priority": 2,
                "base_relevance": 0.78,
                "keywords": [
                    "cryptography",
                    "cryptographic",
                    "privacy",
                    "digital forensics",
                    "digital forensic",
                    "computer forensics",
                    "computer forensic",
                    "cyber forensics",
                    "incident response",
                    "security engineering",
                ],
            },
        ],
        "weights": {
            "relevance": 0.45,
            "recency": 0.25,
            "format": 0.15,
            "affordability": 0.15,
        },
    },
}


SECURITY_CONTEXT_TERMS = [
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
    "forensic",
    "forensics",
    "incident response",
]

SECURITY_EXCLUSION_TERMS = [
    "food security",
    "energy security",
    "social security",
    "national security",
    "human security",
    "water security",
    "health security",
]


def get_scenario(scenario_id):
    """Return a validated scenario specification."""
    scenario_id = str(scenario_id).upper()
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Use 'S1' or 'S2'.")
    return SCENARIOS[scenario_id]
