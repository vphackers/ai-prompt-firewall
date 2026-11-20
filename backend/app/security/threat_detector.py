
# Known suspicious phrases and their classifications

THREAT_KEYWORDS = {
    "PROMPT_INJECTION": [
        "ignore previous instructions",
        "ignore all previous instructions",
        "disregard previous instructions",
        "forget your instructions",
        "bypass safety restrictions",
    ],

    "SYSTEM_PROMPT_EXTRACTION": [
        "reveal system prompt",
        "show me your system prompt",
        "print your system prompt",
        "reveal hidden instructions",
    ],
}


def detect_keyword_threats(normalized_prompt: str) -> list:
    """
    Detect known suspicious phrases in normalized text.

    This function identifies security signals.
    It does not make the final blocking decision.
    """

    findings = []

    for category, keywords in THREAT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in normalized_prompt:

                findings.append({
                    "category": category,
                    "matched_keyword": keyword,
                    "severity": "HIGH"
                })

    return findings
