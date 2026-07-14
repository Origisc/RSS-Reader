from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QMainWindow,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Mercury")
        self.resize(1200, 720)

        self.feed_list = QListWidget()
        self.article_list = QListWidget()
        self.article_reader = QTextBrowser()

        self._setup_ui()
        self._load_mock_data()
        self._connect_signals()

    def _setup_ui(self) -> None:
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("订阅源"))
        left_layout.addWidget(self.feed_list)

        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("文章列表"))
        middle_layout.addWidget(self.article_list)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("阅读区"))
        right_layout.addWidget(self.article_reader)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)

        splitter.setSizes([220, 320, 660])

        self.setCentralWidget(splitter)

    def _load_mock_data(self) -> None:
        self.feed_list.addItems(
            [
                "OpenAI Blog",
                "Python Weekly",
                "Hacker News",
            ]
        )

        self.article_list.addItems(
            [
                "Mercury 项目启动",
                "PySide6 三栏布局",
                "如何设计本地优先应用",
            ]
        )

        self.article_reader.setHtml(
            """
            <h1>欢迎使用 Mercury</h1>
            <p>这是一个使用 PySide6 创建的 RSS 阅读器界面。</p>
            <p>当前内容为 Mock 数据，还没有连接数据库和 Feed 服务。</p>
            """
        )

    def _connect_signals(self) -> None:
        self.article_list.currentTextChanged.connect(
            self._show_selected_article
        )

    def _show_selected_article(self, title: str) -> None:
        if not title:
            return

        self.article_reader.setHtml(
            f"""
            <h1>{title}</h1>
            <p><strong>来源：</strong>Mock Feed</p>
            <p>
                这是文章“{title}”的示例正文。
                目前界面使用假数据，因此不需要等待成员 A。
            </p>
            """
        )