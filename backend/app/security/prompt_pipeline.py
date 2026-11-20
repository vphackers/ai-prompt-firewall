
from app.security.normalizer import normalize_for_detection

from app.security.threat_engine import analyze_threats

from app.security.risk_engine import calculate_risk


def inspect_prompt(prompt: str) -> dict:
    """
    Run the complete prompt security inspection pipeline.

    Steps:
    1. Normalize the prompt.
    2. Detect security threats.
    3. Calculate risk score.
    4. Return the final security analysis.
    """

    # Step 1: Normalize the prompt
    normalized_prompt = normalize_for_detection(prompt)

    # Step 2: Run the threat detection engine
    detection_result = analyze_threats(normalized_prompt)

    # Step 3: Extract individual threat findings
    findings = detection_result["findings"]

    # Step 4: Calculate risk
    risk_result = calculate_risk(findings)

    # Step 5: Combine all results
    return {
        "is_suspicious": detection_result["is_suspicious"],
        "total_findings": detection_result["total_findings"],
        "findings": findings,
        "risk_score": risk_result["risk_score"],
        "risk_status": risk_result["risk_status"],
        "detected_categories": risk_result["detected_categories"]
    }
