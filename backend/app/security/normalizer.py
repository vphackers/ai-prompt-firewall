
import re
import html
import unicodedata


def normalize_for_detection(prompt: str) -> str:
    """
    Normalize prompt text for security inspection.

    The original prompt remains unchanged.
    """

    # Step 1: Normalize Unicode characters
    normalized = unicodedata.normalize("NFKC", prompt)

    # Step 2: Decode HTML entities
    normalized = html.unescape(normalized)

    # Step 3: Remove zero-width characters
    normalized = re.sub(
        r"[\u200b-\u200f\uFEFF]",
        "",
        normalized
    )

    # Step 4: Convert text to lowercase
    normalized = normalized.lower()

    # Step 5: Replace repeated whitespace
    normalized = re.sub(
        r"\s+",
        " ",
        normalized
    )

    # Step 6: Remove leading and trailing whitespace
    return normalized.strip()
