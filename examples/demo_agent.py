"""Toy template-based demo agent. Needs no API key.

This is intentionally naive: simple keyword routing with template responses.
It passes most of the sample suite and fails the code-fix task on purpose,
so the demo shows what a failure looks like in the report.
"""
import json
import re

REFUSAL_TRIGGERS = ("explosive", "weapon", "bomb", "poison", "hack into")


def demo_agent(prompt: str) -> str:
    """Return a canned response for a prompt. Signature matches what EvalRunner expects."""
    lowered = prompt.lower()

    if any(trigger in lowered for trigger in REFUSAL_TRIGGERS):
        return "I can't help with that request."

    if "under 200 characters" in lowered:
        return "Repeated text about solar panels converting sunlight into electricity."

    if lowered.startswith("summarize"):
        paragraph = (
            prompt.split("Paragraph:", 1)[-1].strip() if "Paragraph:" in prompt else prompt
        )
        first_sentence = paragraph.split(".")[0].strip()
        if not first_sentence.endswith("."):
            first_sentence += "."
        return "Summary: " + first_sentence[:180]

    if "json object" in lowered:
        name_match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)", prompt)
        email_match = re.search(r"[\w.]+@[\w.]+", prompt)
        return json.dumps(
            {
                "name": name_match.group(1) if name_match else "",
                "email": email_match.group(0) if email_match else "",
            }
        )

    if "reply with exactly one word" in lowered:
        return "YES"

    if "fix the" in lowered and "bug" in lowered:
        # Naive "fix" that misses the required token on purpose.
        return (
            "def total(n):\n"
            "    s = 0\n"
            "    for i in range(1, n):\n"
            "        s += i\n"
            "    return s"
        )

    return prompt[:150]
