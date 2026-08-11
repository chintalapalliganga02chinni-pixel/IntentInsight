"""Build semantic intent text from pull-request metadata."""

from __future__ import annotations


def build_intent_text(
    *,
    title: str,
    description: str,
) -> str:
    """Build the text representation used for semantic encoding."""

    clean_title = title.strip()
    clean_description = description.strip()

    if clean_description:
        return (
            "Pull request title:\n"
            f"{clean_title}\n\n"
            "Pull request description:\n"
            f"{clean_description}"
        )

    return f"Pull request title:\n{clean_title}"