"""String utilities to be used across application."""


def check_str_not_null(val: str | None):
    """Cheks if the string is not null and doesn't equal 'null'."""
    return val is not None and val != "" and val != "null"
