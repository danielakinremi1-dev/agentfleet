"""Checks for values that pass JSON parsing but that PostgreSQL cannot store.

Rejecting them during validation turns what would be a database error (a 500) into a normal
validation error (a 422) that tells the client what to change.
"""

NUL = "\x00"


def contains_nul(value: object) -> bool:
    """Whether any string inside a parsed JSON value, keys included, contains the NUL character.

    PostgreSQL cannot store NUL in `text` or `jsonb`, although JSON allows it as `\\u0000`.
    """
    if isinstance(value, str):
        return NUL in value
    if isinstance(value, dict):
        return any(contains_nul(key) or contains_nul(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_nul(item) for item in value)
    return False
