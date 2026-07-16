DEFAULT_LANGUAGE = "zh_CN"

SUPPORTED_LANGUAGES = {
    "zh_CN": "简体中文",
    "en_US": "English",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh_CN": {
        "app.title": "Mercury",
        "menu.file": "文件",
        "menu.settings": "设置",
        "menu.view": "视图",
        "menu.help": "帮助",
        "action.add_feed": "添加 Feed",
        "action.import_opml": "导入 OPML",
        "action.refresh": "刷新",
        "action.preferences": "首选项",
        "action.toggle_tags_panel": "标签面板",
        "action.exit": "退出",
        "action.about": "关于 Mercury",
        "toolbar.main": "主工具栏",
        "sidebar.title": "Feeds",
        "sidebar.tab.feeds": "Feeds",
        "sidebar.tab.tags": "Tags",
        "sidebar.feed_detail": "{count} 未读",
        "sidebar.footer": "Feeds: 3 · Entries: 本地缓存",
        "article_list.title": "Entries",
        "article_list.filter.unread": "未读",
        "article_list.entry_meta": "本地缓存条目",
        "article_reader.title": "Reader",
        "article_reader.welcome_title": "欢迎使用 Mercury",
        "article_reader.welcome_body": "添加或导入订阅源，然后刷新并选择文章。",
        "article_reader.source_label": "来源",
        "article_reader.local_note": (
            "本视图展示本地缓存内容；摘要、翻译和标签建议需要用户主动配置后再调用 Provider。"
        ),
        "reader.view.raw": "原始内容",
        "reader.view.cleaned_html": "Cleaned HTML",
        "reader.view.markdown": "Markdown",
        "reader.status.raw": "正在显示原始内容",
        "reader.status.cleaned_html": "正在显示 Cleaned HTML",
        "reader.status.markdown": "正在显示 Cleaned Markdown",
        "reader.status.fallback_unavailable": "{view} 暂不可用，已显示原始内容。",
        "reader.status.fallback_error": "清洗失败：{error}。已显示原始内容。",
        "feed.add_dialog.title": "添加 Feed",
        "feed.add_dialog.label": "Feed URL：",
        "opml.import_dialog.title": "导入 OPML",
        "opml.import_dialog.filter": "OPML 文件 (*.opml *.xml);;所有文件 (*)",
        "settings.title": "设置",
        "settings.language": "界面语言：",
        "settings.theme": "界面主题：",
        "settings.ok": "确定",
        "settings.cancel": "取消",
        "theme.system": "跟随系统",
        "theme.light": "浅色",
        "theme.dark": "深色",
        "status.settings_applied": "已选择语言：{language}，主题：{theme}",
        "status.add_feed_started": "正在添加 Feed...",
        "status.import_opml_started": "正在导入 OPML...",
        "status.refresh_started": "正在刷新订阅源...",
        "dialog.feature_failed.title": "操作失败",
        "dialog.feature_pending.title": "功能入口已预留",
        "dialog.about.title": "关于 Mercury",
        "dialog.about.body": (
            "<h2>Mercury</h2>"
            "<p>一款本地优先、跨平台的 RSS 阅读器。</p>"
            "<p>当前版本：成员 B UI 原型</p>"
        ),
        "tags.title": "Tags",
        "tags.input_placeholder": "输入标签，逗号分隔",
        "tags.add": "添加",
        "tags.suggested": "Suggested",
        "tags.existing": "Existing",
        "tags.empty": "No tags yet",
        "summary.title": "Summary",
        "summary.collapsed": "⌃ Summary",
    },
    "en_US": {
        "app.title": "Mercury",
        "menu.file": "File",
        "menu.settings": "Settings",
        "menu.view": "View",
        "menu.help": "Help",
        "action.add_feed": "Add Feed",
        "action.import_opml": "Import OPML",
        "action.refresh": "Refresh",
        "action.preferences": "Preferences",
        "action.toggle_tags_panel": "Tags Panel",
        "action.exit": "Exit",
        "action.about": "About Mercury",
        "toolbar.main": "Main Toolbar",
        "sidebar.title": "Feeds",
        "sidebar.tab.feeds": "Feeds",
        "sidebar.tab.tags": "Tags",
        "sidebar.feed_detail": "{count} unread",
        "sidebar.footer": "Feeds: 3 · Entries: local cache",
        "article_list.title": "Entries",
        "article_list.filter.unread": "Unread",
        "article_list.entry_meta": "Local cached entry",
        "article_reader.title": "Reader",
        "article_reader.welcome_title": "Welcome to Mercury",
        "article_reader.welcome_body": "Add or import feeds, refresh, then select an article.",
        "article_reader.source_label": "Source",
        "article_reader.local_note": (
            "This view renders local cached content; summary, translation, and tag suggestions "
            "will call a Provider only after the user configures and starts them."
        ),
        "reader.view.raw": "Original",
        "reader.view.cleaned_html": "Cleaned HTML",
        "reader.view.markdown": "Markdown",
        "reader.status.raw": "Showing original content",
        "reader.status.cleaned_html": "Showing cleaned HTML",
        "reader.status.markdown": "Showing cleaned Markdown",
        "reader.status.fallback_unavailable": (
            "{view} is unavailable; showing original content."
        ),
        "reader.status.fallback_error": (
            "Cleaning failed: {error}. Showing original content."
        ),
        "feed.add_dialog.title": "Add Feed",
        "feed.add_dialog.label": "Feed URL:",
        "opml.import_dialog.title": "Import OPML",
        "opml.import_dialog.filter": "OPML files (*.opml *.xml);;All files (*)",
        "settings.title": "Settings",
        "settings.language": "Interface language:",
        "settings.theme": "Interface theme:",
        "settings.ok": "OK",
        "settings.cancel": "Cancel",
        "theme.system": "Use system setting",
        "theme.light": "Light",
        "theme.dark": "Dark",
        "status.settings_applied": "Selected language: {language}; theme: {theme}",
        "status.add_feed_started": "Adding feed...",
        "status.import_opml_started": "Importing OPML...",
        "status.refresh_started": "Refreshing feeds...",
        "dialog.feature_failed.title": "Action Failed",
        "dialog.feature_pending.title": "Feature Entry Ready",
        "dialog.about.title": "About Mercury",
        "dialog.about.body": (
            "<h2>Mercury</h2>"
            "<p>A local-first, cross-platform RSS reader.</p>"
            "<p>Current version: Member B UI prototype</p>"
        ),
        "tags.title": "Tags",
        "tags.input_placeholder": "Type tags (comma-separated)",
        "tags.add": "Add",
        "tags.suggested": "Suggested",
        "tags.existing": "Existing",
        "tags.empty": "No tags yet",
        "summary.title": "Summary",
        "summary.collapsed": "⌃ Summary",
    },
}


class Translator:
    """Small runtime translator for UI strings."""

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self._language = DEFAULT_LANGUAGE
        self.set_language(language)

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in TRANSLATIONS:
            self._language = DEFAULT_LANGUAGE
            return

        self._language = language

    def text(self, key: str) -> str:
        current = TRANSLATIONS.get(self._language, {})
        fallback = TRANSLATIONS[DEFAULT_LANGUAGE]
        return current.get(key) or fallback.get(key) or key
