import re

_SIMPLE_PROPERTY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def append_json_path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]"
    if _SIMPLE_PROPERTY.fullmatch(key):
        return f"{parent}.{key}"
    escaped = key.replace("\\", "\\\\").replace("'", "\\'")
    return f"{parent}['{escaped}']"
