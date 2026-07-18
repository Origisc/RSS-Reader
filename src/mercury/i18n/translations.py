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
        "action.delete_feed": "删除所选 Feed",
        "action.mark_read": "标记为已读",
        "action.mark_unread": "标记为未读",
        "action.preferences": "首选项",
        "action.ai_settings": "AI 设置",
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
        "feed.delete_dialog.title": "删除 Feed",
        "feed.delete_dialog.body": (
            "确定删除订阅源“{title}”及其本地缓存文章吗？此操作不可撤销。"
        ),
        "feed.delete_unavailable": (
            "删除服务未配置；当前不会修改本地订阅或文章。"
        ),
        "feed.delete_failed": "删除失败：订阅源不存在或本地数据库操作失败。",
        "opml.import_dialog.title": "导入 OPML",
        "opml.import_dialog.filter": "OPML 文件 (*.opml *.xml);;所有文件 (*)",
        "settings.title": "设置",
        "settings.language": "界面语言：",
        "settings.theme": "界面主题：",
        "settings.reader_font_size": "正文字号：",
        "settings.reader_line_height": "正文行高：",
        "settings.reader_content_width": "正文宽度：",
        "settings.ok": "确定",
        "settings.cancel": "取消",
        "ai_settings.title": "AI Provider 设置",
        "ai_settings.base_url": "Base URL：",
        "ai_settings.model": "模型：",
        "ai_settings.api_key": "API Key（可选）：",
        "ai_settings.timeout": "超时时间：",
        "ai_settings.privacy_notice": (
            "文章内容只会在你主动触发摘要、翻译等 AI 功能时发送给已配置的 Provider；"
            "未配置 AI 也不会影响基础阅读。"
        ),
        "ai_settings.test_connection": "测试连接",
        "ai_settings.invalid_config": "请填写有效的 Base URL、模型和超时时间。",
        "ai_settings.connection_unavailable": (
            "当前未接入 Provider 连接适配器；配置尚未发送到网络。"
        ),
        "ai_settings.connection_success": "连接测试成功。",
        "ai_settings.connection_failed": "连接测试失败。",
        "theme.system": "跟随系统",
        "theme.light": "浅色",
        "theme.dark": "深色",
        "status.settings_applied": (
            "已应用语言：{language}，主题：{theme}，正文字号：{font_size}px"
        ),
        "status.ai_settings_saved": "AI Provider 配置已在本次运行中保存。",
        "status.add_feed_started": "正在添加 Feed...",
        "status.import_opml_started": "正在导入 OPML...",
        "status.refresh_started": "正在刷新订阅源...",
        "status.delete_feed_started": "正在删除 Feed...",
        "status.delete_feed_finished": "已删除 Feed：{title}",
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
        "summary.language": "摘要语言：",
        "summary.language.same": "与原文相同",
        "summary.language.zh_cn": "简体中文",
        "summary.language.en_us": "英文",
        "summary.detail": "详细程度：",
        "summary.detail.brief": "简略",
        "summary.detail.standard": "标准",
        "summary.detail.detailed": "详细",
        "summary.custom_prompt": "自定义 Prompt：",
        "summary.custom_prompt_placeholder": "可选；留空时使用默认摘要 Prompt",
        "summary.content_placeholder": "生成的摘要会显示在这里。",
        "summary.generate": "生成摘要",
        "summary.regenerate": "重新生成",
        "summary.configure_ai": "AI 设置",
        "summary.generated_at": "生成时间：{time}",
        "summary.status.no_article": "选择一篇文章后可以生成摘要。",
        "summary.status.unavailable": "摘要服务尚不可用，请检查 AI Provider 设置。",
        "summary.status.ready": "摘要会在你主动点击生成后发送文章内容。",
        "summary.status.running": "正在后台生成摘要，正文仍可阅读……",
        "summary.status.generated": "摘要已生成。",
        "summary.status.storage_warning": "摘要已生成，但未能保存到本地。",
        "summary.error.invalid_input": "当前文章没有可用于摘要的正文。",
        "summary.error.provider_not_configured": "请先配置 AI Provider。",
        "summary.error.provider_failure": "摘要生成失败，文章正文仍可正常阅读。",
        "summary.error.empty_response": "Provider 没有返回摘要内容。",
        "summary.error.load_failed": "本地摘要读取失败，可以重新生成。",
        "summary.error.unexpected": "摘要操作失败，文章正文未受影响。",
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
        "action.delete_feed": "Delete selected Feed",
        "action.mark_read": "Mark as read",
        "action.mark_unread": "Mark as unread",
        "action.preferences": "Preferences",
        "action.ai_settings": "AI Settings",
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
        "feed.delete_dialog.title": "Delete Feed",
        "feed.delete_dialog.body": (
            "Delete the feed “{title}” and its locally cached articles? "
            "This action cannot be undone."
        ),
        "feed.delete_unavailable": (
            "The deletion service is not configured. "
            "No local feeds or articles were changed."
        ),
        "feed.delete_failed": (
            "Deletion failed because the feed was not found or the local database operation failed."
        ),
        "opml.import_dialog.title": "Import OPML",
        "opml.import_dialog.filter": "OPML files (*.opml *.xml);;All files (*)",
        "settings.title": "Settings",
        "settings.language": "Interface language:",
        "settings.theme": "Interface theme:",
        "settings.reader_font_size": "Reader font size:",
        "settings.reader_line_height": "Reader line height:",
        "settings.reader_content_width": "Reader content width:",
        "settings.ok": "OK",
        "settings.cancel": "Cancel",
        "ai_settings.title": "AI Provider Settings",
        "ai_settings.base_url": "Base URL:",
        "ai_settings.model": "Model:",
        "ai_settings.api_key": "API Key (optional):",
        "ai_settings.timeout": "Timeout:",
        "ai_settings.privacy_notice": (
            "Article content is sent to the configured Provider only when you explicitly "
            "start an AI action such as summary or translation. Basic reading works without AI."
        ),
        "ai_settings.test_connection": "Test Connection",
        "ai_settings.invalid_config": (
            "Enter a valid Base URL, model, and timeout."
        ),
        "ai_settings.connection_unavailable": (
            "No Provider connection adapter is available; the configuration was not sent "
            "over the network."
        ),
        "ai_settings.connection_success": "Connection test succeeded.",
        "ai_settings.connection_failed": "Connection test failed.",
        "theme.system": "Use system setting",
        "theme.light": "Light",
        "theme.dark": "Dark",
        "status.settings_applied": (
            "Applied language: {language}; theme: {theme}; "
            "reader font: {font_size}px"
        ),
        "status.ai_settings_saved": "AI Provider settings saved for this session.",
        "status.add_feed_started": "Adding feed...",
        "status.import_opml_started": "Importing OPML...",
        "status.refresh_started": "Refreshing feeds...",
        "status.delete_feed_started": "Deleting feed...",
        "status.delete_feed_finished": "Deleted feed: {title}",
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
        "summary.language": "Summary language:",
        "summary.language.same": "Same as article",
        "summary.language.zh_cn": "Simplified Chinese",
        "summary.language.en_us": "English",
        "summary.detail": "Detail level:",
        "summary.detail.brief": "Brief",
        "summary.detail.standard": "Standard",
        "summary.detail.detailed": "Detailed",
        "summary.custom_prompt": "Custom prompt:",
        "summary.custom_prompt_placeholder": (
            "Optional; leave empty to use the default summary prompt"
        ),
        "summary.content_placeholder": "The generated summary appears here.",
        "summary.generate": "Generate Summary",
        "summary.regenerate": "Regenerate",
        "summary.configure_ai": "AI Settings",
        "summary.generated_at": "Generated: {time}",
        "summary.status.no_article": "Select an article to generate a summary.",
        "summary.status.unavailable": (
            "The summary service is unavailable; check AI Provider settings."
        ),
        "summary.status.ready": (
            "Article content is sent only after you start summary generation."
        ),
        "summary.status.running": (
            "Generating in the background; the article remains readable…"
        ),
        "summary.status.generated": "Summary generated.",
        "summary.status.storage_warning": (
            "Summary generated but could not be saved locally."
        ),
        "summary.error.invalid_input": (
            "This article has no readable content to summarize."
        ),
        "summary.error.provider_not_configured": (
            "Configure an AI Provider first."
        ),
        "summary.error.provider_failure": (
            "Summary generation failed; the article remains readable."
        ),
        "summary.error.empty_response": (
            "The Provider returned no summary content."
        ),
        "summary.error.load_failed": (
            "The local summary could not be loaded; you can regenerate it."
        ),
        "summary.error.unexpected": (
            "The summary action failed; the article was not affected."
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
