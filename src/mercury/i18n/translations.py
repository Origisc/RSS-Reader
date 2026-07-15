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
        "action.refresh": "刷新",
        "action.preferences": "首选项",
        "action.toggle_ai_panel": "AI 面板",
        "action.exit": "退出",
        "action.about": "关于 Mercury",
        "toolbar.main": "主工具栏",
        "sidebar.title": "订阅源",
        "article_list.title": "文章列表",
        "article_reader.title": "阅读区",
        "article_reader.welcome_title": "欢迎使用 Mercury",
        "article_reader.welcome_body": "请从文章列表中选择一篇文章。",
        "article_reader.source_label": "来源",
        "settings.title": "设置",
        "settings.language": "界面语言：",
        "settings.theme": "界面主题：",
        "settings.ok": "确定",
        "settings.cancel": "取消",
        "theme.system": "跟随系统",
        "theme.light": "浅色",
        "theme.dark": "深色",
        "status.settings_applied": "已选择语言：{language}，主题：{theme}",
        "status.add_feed_pending": "添加 Feed 入口已预留，等待 FeedService 接入。",
        "status.refresh_pending": "刷新入口已预留，等待 SyncService 接入。",
        "dialog.feature_pending.title": "功能入口已预留",
        "dialog.about.title": "关于 Mercury",
        "dialog.about.body": (
            "<h2>Mercury</h2>"
            "<p>一款本地优先、跨平台的 RSS 阅读器。</p>"
            "<p>当前版本：成员 B UI 原型</p>"
        ),
        "ai_panel.title": "AI",
        "ai_panel.body": (
            "摘要和翻译入口已预留。\n\n"
            "后续会通过可配置的 LLM Provider 调用；在用户主动配置并触发前，"
            "不会发送文章内容。"
        ),
    },
    "en_US": {
        "app.title": "Mercury",
        "menu.file": "File",
        "menu.settings": "Settings",
        "menu.view": "View",
        "menu.help": "Help",
        "action.add_feed": "Add Feed",
        "action.refresh": "Refresh",
        "action.preferences": "Preferences",
        "action.toggle_ai_panel": "AI Panel",
        "action.exit": "Exit",
        "action.about": "About Mercury",
        "toolbar.main": "Main Toolbar",
        "sidebar.title": "Feeds",
        "article_list.title": "Articles",
        "article_reader.title": "Reader",
        "article_reader.welcome_title": "Welcome to Mercury",
        "article_reader.welcome_body": "Select an article from the list.",
        "article_reader.source_label": "Source",
        "settings.title": "Settings",
        "settings.language": "Interface language:",
        "settings.theme": "Interface theme:",
        "settings.ok": "OK",
        "settings.cancel": "Cancel",
        "theme.system": "Use system setting",
        "theme.light": "Light",
        "theme.dark": "Dark",
        "status.settings_applied": "Selected language: {language}; theme: {theme}",
        "status.add_feed_pending": "The Add Feed entry is ready for FeedService integration.",
        "status.refresh_pending": "The Refresh entry is ready for SyncService integration.",
        "dialog.feature_pending.title": "Feature Entry Ready",
        "dialog.about.title": "About Mercury",
        "dialog.about.body": (
            "<h2>Mercury</h2>"
            "<p>A local-first, cross-platform RSS reader.</p>"
            "<p>Current version: Member B UI prototype</p>"
        ),
        "ai_panel.title": "AI",
        "ai_panel.body": (
            "Summary and translation entries are reserved.\n\n"
            "They will call configurable LLM Providers later; article content is not sent "
            "until the user configures a provider and explicitly starts an action."
        ),
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
