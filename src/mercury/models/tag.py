from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tag:
    id: str
    name: str
    article_count: int = 0
