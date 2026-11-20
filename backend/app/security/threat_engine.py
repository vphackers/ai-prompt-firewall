
from app.security.threat_detector import (
    detect_keyword_threats
)

from app.security.regex_detector import (
    detect_regex_threats
)


def analyze_threats(normalized_prompt: str) -> dict:
    """
    Run all available threat detectors
    and combine their findings.
    """

    # Run keyword detection
    keyword_findings = detect_keyword_threats(
        normalized_prompt
    )

    # Run regex detection
    regex_findings = detect_regex_threats(
        normalized_prompt
    )

    # Combine both results
    all_findings = keyword_findings + regex_findings

    # Return unified detection results
    return {
        "is_suspicious": len(all_findings) > 0,
        "total_findings": len(all_findings),
        "findings": all_findings
    }
