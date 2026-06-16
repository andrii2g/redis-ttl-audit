import re


SUSPICIOUS_TERMS = {
    "cache",
    "tmp",
    "temp",
    "session",
    "token",
    "rate",
    "rate-limit",
    "job",
    "lock",
    "queue",
    "worker",
    "request",
    "response",
}


def is_suspicious_persistent_group(group: str) -> bool:
    normalized = group.lower()
    tokens = set(re.split(r"[:_\-]+", normalized))

    for term in SUSPICIOUS_TERMS:
        if term in normalized:
            return True
        term_tokens = term.split("-")
        if all(term_token in tokens for term_token in term_tokens):
            return True

    return False
