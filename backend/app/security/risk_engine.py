
# Risk scores assigned to each threat category

THREAT_SCORES = {
    "PROMPT_INJECTION": 40,
    "SYSTEM_PROMPT_EXTRACTION": 45,
    "XSS": 50,
    "SQL_INJECTION": 50,
}

# Score thresholds

SAFE_THRESHOLD = 20
BLOCKED_THRESHOLD = 50

UNKNOWN_THREAT_SCORE = 10


def calculate_risk(findings: list) -> dict:
    """
    Calculate risk score and classify a prompt.

    Each distinct threat category is counted once.
    """

    risk_score = 0
    detected_categories = set()

    for finding in findings:

        category = finding.get("category")

        if not category:
            continue

        # Avoid counting the same category repeatedly
        if category in detected_categories:
            continue

        detected_categories.add(category)

        # Get the category score
        category_score = THREAT_SCORES.get(
            category,
            UNKNOWN_THREAT_SCORE
        )

        risk_score += category_score

    # Maximum score is 100
    risk_score = min(risk_score, 100)

    # Determine final security status
    if risk_score >= BLOCKED_THRESHOLD:
        risk_status = "BLOCKED"

    elif risk_score >= SAFE_THRESHOLD:
        risk_status = "FLAGGED"

    else:
        risk_status = "SAFE"

    return {
        "risk_score": risk_score,
        "risk_status": risk_status,
        "detected_categories": sorted(detected_categories)
    }
