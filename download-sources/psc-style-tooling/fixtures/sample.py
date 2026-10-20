from pathlib import Path


def load_config(path: Path) -> str:
    with path.open(encoding="utf-8") as source:
        return source.read()


def normalize(value: int) -> int:
    if value < 0:
        return 0
    return value
