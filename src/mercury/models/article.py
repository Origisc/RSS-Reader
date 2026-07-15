from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Feed:
    id: str
    title: str


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    feed_id: str
    title: str
    source_title: str
    content_html: str