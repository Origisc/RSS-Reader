from mercury.models.article import Article, Feed


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