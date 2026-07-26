from dataclasses import replace

from mercury.models.article import Article, Feed
from mercury.models.tag import Tag
from mercury.services.article_service import StarredEntryError
from mercury.services.tag_service import TagServiceError


class MockArticleService:
    """供 UI 独立开发和测试使用的假数据服务。"""

    def __init__(self) -> None:
        self._feeds = [
            Feed(id="openai", title="OpenAI Blog"),
            Feed(id="python-weekly", title="Python Weekly"),
            Feed(id="hacker-news", title="Hacker News"),
        ]

        self._articles = [
            Article(
                id="mercury-start",
                feed_id="openai",
                title="Mercury 项目启动",
                source_title="OpenAI Blog",
                content_html=(
                    "<p>Mercury 是一个使用 PySide6 构建的本地优先 "
                    "RSS 阅读器。</p>"
                ),
            ),
            Article(
                id="pyside-layout",
                feed_id="python-weekly",
                title="PySide6 三栏布局",
                source_title="Python Weekly",
                content_html=(
                    "<p>本界面由订阅源、文章列表和阅读区三个区域组成。</p>"
                ),
            ),
            Article(
                id="local-first",
                feed_id="hacker-news",
                title="如何设计本地优先应用",
                source_title="Hacker News",
                content_html=(
                    "<p>本地优先应用应默认将用户数据保存在本地，"
                    "并避免不必要的数据上传。</p>"
                ),
            ),
        ]
        self._tags: list[Tag] = []
        self._article_tag_ids: dict[str, set[str]] = {
            article.id: set() for article in self._articles
        }
        self._next_tag_id = 1

    def list_feeds(self) -> list[Feed]:
        return list(self._feeds)

    def list_articles(self, feed_id: str | None = None) -> list[Article]:
        if feed_id is None:
            return list(self._articles)

        return [
            article
            for article in self._articles
            if article.feed_id == feed_id
        ]

    def get_article(self, article_id: str) -> Article | None:
        for article in self._articles:
            if article.id == article_id:
                return article

        return None

    def set_starred(self, article_id: str, is_starred: bool) -> None:
        for index, article in enumerate(self._articles):
            if article.id != article_id:
                continue

            self._articles[index] = replace(
                article,
                is_starred=is_starred,
            )
            return

        raise StarredEntryError("Article not found.")

    def list_starred_articles(self) -> list[Article]:
        return [
            article for article in self._articles if article.is_starred
        ]

    def count_starred_articles(self) -> int:
        return sum(article.is_starred for article in self._articles)

    def list_tags(self) -> list[Tag]:
        counts = {
            tag.id: sum(
                tag.id in assigned_ids
                for assigned_ids in self._article_tag_ids.values()
            )
            for tag in self._tags
        }
        return [
            replace(tag, article_count=counts[tag.id])
            for tag in self._tags
        ]

    def list_article_tags(self, article_id: str) -> list[Tag]:
        assigned_ids = self._article_tags_for(article_id)
        return [
            tag for tag in self.list_tags() if tag.id in assigned_ids
        ]

    def create_tag(self, name: str) -> Tag:
        normalized = self._normalized_tag_name(name)
        existing = next(
            (
                tag
                for tag in self._tags
                if tag.name.casefold() == normalized.casefold()
            ),
            None,
        )
        if existing is not None:
            return next(
                tag for tag in self.list_tags() if tag.id == existing.id
            )

        tag = Tag(id=str(self._next_tag_id), name=normalized)
        self._next_tag_id += 1
        self._tags.append(tag)
        return tag

    def rename_tag(self, tag_id: str, new_name: str) -> Tag:
        normalized = self._normalized_tag_name(new_name)
        tag_index = self._tag_index(tag_id)
        if any(
            tag.id != tag_id
            and tag.name.casefold() == normalized.casefold()
            for tag in self._tags
        ):
            raise TagServiceError(
                "A tag with that name already exists."
            )

        self._tags[tag_index] = replace(
            self._tags[tag_index],
            name=normalized,
        )
        return next(
            tag for tag in self.list_tags() if tag.id == tag_id
        )

    def delete_tag(self, tag_id: str) -> None:
        tag_index = self._tag_index(tag_id)
        self._tags.pop(tag_index)
        for assigned_ids in self._article_tag_ids.values():
            assigned_ids.discard(tag_id)

    def add_tag_to_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        assigned_ids = self._article_tags_for(article_id)
        self._tag_index(tag_id)
        assigned_ids.add(tag_id)

    def remove_tag_from_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        assigned_ids = self._article_tags_for(article_id)
        self._tag_index(tag_id)
        assigned_ids.discard(tag_id)

    def list_articles_by_tags(
        self,
        tag_ids: list[str],
    ) -> list[Article]:
        selected_ids = set(tag_ids)
        if not selected_ids:
            return []
        for tag_id in selected_ids:
            self._tag_index(tag_id)
        return [
            article
            for article in self._articles
            if selected_ids.issubset(
                self._article_tag_ids.get(article.id, set())
            )
        ]

    def fetch_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return (
            "Mock fetch article content request received: "
            f"{article_id}, force={force}"
        )

    def clean_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return (
            "Mock clean article content request received: "
            f"{article_id}, force={force}"
        )

    def convert_to_markdown(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return (
            "Mock convert to markdown request received: "
            f"{article_id}, force={force}"
        )

    def translate_article_content(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        return (
            "Mock translate article content request received: "
            f"{article_id}, target_language={target_language}, force={force}"
        )

    def add_feed(self, xml_url: str) -> str:
        return f"Mock add feed request received: {xml_url}"

    def import_opml(self, file_path: str) -> str:
        return f"Mock OPML import request received: {file_path}"

    def refresh_all(self) -> str:
        return "Mock feeds refreshed."

    @staticmethod
    def _normalized_tag_name(name: str) -> str:
        normalized = " ".join(str(name).split())
        if not normalized:
            raise TagServiceError("Tag name cannot be empty.")
        if len(normalized) > 64:
            raise TagServiceError("Tag name is too long.")
        return normalized

    def _tag_index(self, tag_id: str) -> int:
        for index, tag in enumerate(self._tags):
            if tag.id == str(tag_id):
                return index
        raise TagServiceError("Tag not found.")

    def _article_tags_for(self, article_id: str) -> set[str]:
        if self.get_article(article_id) is None:
            raise TagServiceError("Article not found.")
        return self._article_tag_ids.setdefault(article_id, set())
