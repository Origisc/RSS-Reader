import xml.etree.ElementTree as ET

from domain.feed.import_errors import (
    FeedImportError,
    FeedImportErrorCode,
)
from domain.feed.source_paths import (
    read_utf8_file,
    resolve_feed_source,
    resolve_local_file,
)


def import_opml(feed_use_case, file_path: str) -> int:
    opml_path = resolve_local_file(file_path)
    document = read_utf8_file(opml_path)

    try:
        root = ET.fromstring(document)
    except ET.ParseError as exc:
        raise FeedImportError(
            FeedImportErrorCode.INVALID_OPML,
            source=str(opml_path),
            detail=str(exc),
        ) from exc

    if _local_name(root.tag).casefold() != "opml":
        raise FeedImportError(
            FeedImportErrorCode.INVALID_OPML,
            source=str(opml_path),
            detail="The root element must be <opml>.",
        )

    feeds: list[tuple[str, str, object]] = []
    seen_sources: set[str] = set()
    for outline in root.iter():
        if _local_name(outline.tag).casefold() != "outline":
            continue

        xml_url = str(outline.get("xmlUrl") or "").strip()
        if not xml_url:
            continue

        resolved = resolve_feed_source(
            xml_url,
            base_directory=opml_path.parent,
        )
        canonical_source, feed_data = (
            feed_use_case.prepare_feed_source(resolved.value)
        )
        deduplication_key = canonical_source.casefold()
        if deduplication_key in seen_sources:
            continue
        seen_sources.add(deduplication_key)

        title = str(
            outline.get("text")
            or outline.get("title")
            or "Unnamed feed"
        ).strip()
        feeds.append(
            (
                title or "Unnamed feed",
                canonical_source,
                feed_data,
            )
        )

    if not feeds:
        raise FeedImportError(
            FeedImportErrorCode.OPML_NO_FEEDS,
            source=str(opml_path),
        )

    try:
        for title, xml_url, feed_data in feeds:
            feed_use_case.add_prepared_feed(
                xml_url,
                feed_data,
                title_override=title,
            )
    except Exception as exc:
        raise FeedImportError(
            FeedImportErrorCode.STORAGE_FAILED,
            source=str(opml_path),
            detail=str(exc),
        ) from exc

    return len(feeds)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
