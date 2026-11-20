
import re


REGEX_RULES = {
    "XSS": [
        r"<\s*script\b",
        r"\bon\w+\s*=",
        r"javascript\s*:",
        r"<\s*svg\b",
        r"<\s*iframe\b",
    ],

    "SQL_INJECTION": [
        r"\bunion\s+select\b",
        r"\bselect\b.+\bfrom\b",
        r"\bdrop\s+table\b",
        r"\bdelete\s+from\b",
        r"\binsert\s+into\b",
    ]
}


def detect_regex_threats(normalized_prompt: str) -> list:
    """
    Detect suspicious patterns using regex.
    """

    findings = []

    for category, patterns in REGEX_RULES.items():

        for pattern in patterns:

            if re.search(pattern, normalized_prompt, re.IGNORECASE):

                findings.append({
                    "category": category,
                    "matched_pattern": pattern,
                    "severity": "HIGH"
                })

    return findings
