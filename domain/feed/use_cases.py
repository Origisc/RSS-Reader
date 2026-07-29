from pathlib import Path

import feedparser
import requests

from core.database import DBManager
from domain.feed.import_errors import (
    FeedImportError,
    FeedImportErrorCode,
)
from domain.feed.source_paths import (
    read_utf8_file,
    resolve_feed_source,
)


class FeedUseCase:
    def __init__(self, db: DBManager):
        self.db = db

    def add_single_feed(self, xml_url: str) -> int:
        canonical_source, feed_data = self._load_feed(xml_url)
        feed_title = feed_data.feed.get("title", canonical_source)
        html_url = feed_data.feed.get("link", "")

        try:
            feed_id = self.db.add_feed(
                feed_title,
                canonical_source,
                html_url,
            )
            self.db.save_articles(feed_id, feed_data.entries)
        except Exception as exc:
            raise FeedImportError(
                FeedImportErrorCode.STORAGE_FAILED,
                source=canonical_source,
                detail=str(exc),
            ) from exc

        return int(feed_id)

    def validate_feed_source(
        self,
        source: str,
        *,
        base_directory: Path | None = None,
    ) -> str:
        canonical_source, _feed_data = self._load_feed(
            source,
            base_directory=base_directory,
        )
        return canonical_source

    def refresh_all(self) -> None:
        feeds = self.db.get_all_feeds()
        print(f"开始刷新全部 {len(feeds)} 个订阅源...")
        for feed_id, title, xml_url in feeds:
            try:
                _canonical_source, feed_data = self._load_feed(xml_url)
                self.db.save_articles(feed_id, feed_data.entries)
                print(f"已更新: {title}")
            except FeedImportError as exc:
                print(f"更新失败 [{title}]: {exc}")

    def remove_feed_by_id(self, feed_id: int) -> dict:
        """
        【新功能】根据 ID 删除订阅源业务用例
        返回状态字典，完美适配未来的 PySide6 异步信号回传
        """
        print(f"正在尝试删除订阅源 ID: {feed_id} ...")

        success = self.db.delete_feed(feed_id)

        if success:
            print(f"成功删除订阅源 [ID: {feed_id}] 及其关联文章。")
            return {"success": True, "message": "订阅源已成功取消订阅。"}

        print(f"删除失败，未找到 ID 为 {feed_id} 的订阅源。")
        return {
            "success": False,
            "message": "删除失败：未找到该订阅源或数据库异常。",
        }

    def _load_feed(
        self,
        source: str,
        *,
        base_directory: Path | None = None,
    ) -> tuple[str, object]:
        resolved = resolve_feed_source(
            source,
            base_directory=base_directory,
        )
        if resolved.local_path is not None:
            payload: str | bytes = read_utf8_file(resolved.local_path)
        else:
            try:
                response = requests.get(resolved.value, timeout=10)
                response.raise_for_status()
                payload = response.content
            except requests.RequestException as exc:
                raise FeedImportError(
                    FeedImportErrorCode.NETWORK_FAILED,
                    source=resolved.value,
                    detail=str(exc),
                ) from exc

        feed_data = feedparser.parse(payload)
        if not getattr(feed_data, "version", ""):
            detail = str(getattr(feed_data, "bozo_exception", "") or "")
            raise FeedImportError(
                FeedImportErrorCode.INVALID_FEED,
                source=resolved.value,
                detail=detail,
            )

        return resolved.value, feed_data
