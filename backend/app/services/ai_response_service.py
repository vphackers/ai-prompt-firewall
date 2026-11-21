def generate_ai_response(prompt: str) -> str:
    """
    Generate a structured demo response for a prompt
    that has passed the security checks.
    """

    return (
        "Your prompt passed the security checks successfully.\n\n"
        "Accepted prompt:\n"
        f"{prompt.strip()}\n\n"
        "Response mode: Built-in template engine.\n"
        "Note: This demo uses a structured response template. "
        "An external LLM can be connected later."
    )