def format_int(value: int) -> str:
    return f"{value:,}"


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def format_seconds(value: int | float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0f}s"
