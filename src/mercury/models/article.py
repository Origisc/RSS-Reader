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
    original_html: str = ""
    fetched_at: str | None = None
    fetch_status: str = "pending"
    fetch_error: str | None = None
    cleaned_html: str = ""
    cleaned_markdown: str = ""
    cleaned_at: str | None = None
    clean_status: str = "pending"
    clean_error: str | None = None
    translated_text: str = ""
    translated_at: str | None = None
    translate_status: str = "pending"
    translate_error: str | None = None
    target_language: str = "zh"