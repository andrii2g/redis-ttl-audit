def group_key(key: str, depth: int) -> str:
    if depth < 1:
        raise ValueError("depth must be greater than 0")

    if key == "":
        return ""

    parts = key.split(":")
    if len(parts) <= depth:
        return key

    return ":".join(parts[:depth])

