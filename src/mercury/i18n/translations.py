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
        "action.star": "添加星标",
        "action.unstar": "取消星标",
        "action.preferences": "首选项",
        "action.ai_settings": "AI 设置",
        "action.toggle_tags_panel": "标签面板",
        "action.toggle_summary_panel": "摘要面板",
        "action.toggle_translation_panel": "翻译设置",
        "action.shortcuts": "快捷键",
        "action.exit": "退出",
        "action.about": "关于 Mercury",
        "toolbar.main": "主工具栏",
        "sidebar.title": "Feeds",
        "sidebar.tab.feeds": "Feeds",
        "sidebar.tab.tags": "Tags",
        "sidebar.feed_detail": "{count} 未读",
        "sidebar.all_feeds": "全部文章",
        "sidebar.starred": "星标",
        "sidebar.starred_detail": "{count} 篇",
        "sidebar.footer": "Feeds: {feeds} · 未读: {unread}",
        "article_list.title": "Entries",
        "article_list.starred_title": "星标",
        "article_list.tags_title": "标签：{tags}",
        "article_list.unread_filter": "未读",
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
        "reader.summary_toggle": "摘要",
        "reader.summary_toggle_tooltip": (
            "显示或隐藏摘要面板（Ctrl+Shift+S）"
        ),
        "reader.translation_toggle": "翻译设置",
        "reader.translation_toggle_tooltip": (
            "显示或隐藏 Reader 内的翻译设置（Ctrl+Shift+T）"
        ),
        "reader.translation_view.bilingual": "双语对照",
        "reader.translation_view.original": "显示原文",
        "reader.translation_view.available_tooltip": (
            "在纯原文和逐段双语阅读之间切换"
        ),
        "reader.translation_view.unavailable_tooltip": (
            "请先生成当前文章的翻译"
        ),
        "reader.status.bilingual": "正在显示逐段双语对照",
        "reader.tags_toggle": "标签",
        "reader.tags_toggle_tooltip": "显示或隐藏当前文章的标签编辑器",
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
        "ai_settings.preset": "配置模板：",
        "ai_settings.preset.custom": "自定义（OpenAI 兼容）",
        "ai_settings.preset.custom_description": (
            "Base URL 和模型均可编辑，适用于兼容 Chat Completions 的服务。"
        ),
        "ai_settings.preset.ollama_qwen25_7b": (
            "本地 Qwen2.5 7B（Ollama，推荐翻译）"
        ),
        "ai_settings.preset.ollama_qwen25_7b_description": (
            "推荐用于中英翻译；零 API 费用，内容只发送到本机 "
            "127.0.0.1，无需 API Key。使用前请执行："
            "ollama pull qwen2.5:7b-instruct"
        ),
        "ai_settings.preset.ollama_deepseek": (
            "本地 DeepSeek（Ollama，零 API 费用）"
        ),
        "ai_settings.preset.ollama_deepseek_description": (
            "零 API 费用，内容只发送到本机 127.0.0.1；无需 API Key。"
            "使用前请安装 Ollama，并执行：ollama pull deepseek-r1:1.5b"
        ),
        "ai_settings.preset.deepseek_api": "DeepSeek 官方 API（按量计费）",
        "ai_settings.preset.deepseek_api_description": (
            "这是云端付费 API，需要 DeepSeek API Key 和可用余额；"
            "它不是免费方案。"
        ),
        "ai_settings.base_url": "Base URL：",
        "ai_settings.base_url_placeholder": "例如：https://服务地址/v1",
        "ai_settings.base_url_tooltip": (
            "填写 Chat Completions API 根地址；程序会自动追加 /chat/completions。"
        ),
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
        "status.ai_settings_saved": "AI Provider 配置已保存到本地。",
        "status.ai_settings_storage_failed": (
            "AI Provider 配置未能保存到本地；现有阅读功能不受影响。"
        ),
        "status.add_feed_started": "正在添加 Feed...",
        "status.import_opml_started": "正在导入 OPML...",
        "status.refresh_started": "正在刷新订阅源...",
        "status.article_starred": "已添加星标",
        "status.article_unstarred": "已取消星标",
        "status.star_failed": "无法更新星标，原状态已保留。",
        "status.tags_added": "标签已添加到文章。",
        "status.tag_assigned": "标签已添加到文章。",
        "status.tag_removed": "已从文章移除标签。",
        "status.tag_renamed": "标签已重命名。",
        "status.tag_deleted": "标签已删除。",
        "status.tag_failed": "无法更新本地标签，原有阅读内容不受影响。",
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
        "shortcuts.title": "键盘快捷键",
        "shortcuts.description": "当前页面可用的快捷键及其功能。",
        "shortcuts.key_header": "快捷键",
        "shortcuts.function_header": "功能",
        "shortcuts.show_help": "打开快捷键说明",
        "shortcuts.open_settings": "打开首选项",
        "shortcuts.toggle_summary": "显示或隐藏摘要面板",
        "shortcuts.toggle_translation": "显示或隐藏 Reader 翻译设置",
        "shortcuts.exit": "退出 Mercury",
        "shortcuts.close": "关闭",
        "tags.title": "Tags",
        "tags.browser_hint": "浏览本地标签；文章标签可在 Reader 中编辑。",
        "tags.input_placeholder": "输入标签，逗号分隔",
        "tags.add": "添加",
        "tags.close": "关闭标签编辑器",
        "tags.existing": "已有标签",
        "tags.empty": "还没有标签，请先为当前文章创建一个。",
        "tags.no_article": "选择一篇文章后即可编辑标签。",
        "tags.filter_clear": "清除标签筛选",
        "tags.rename": "重命名",
        "tags.delete": "删除",
        "tags.rename_dialog.title": "重命名标签",
        "tags.rename_dialog.label": "新名称：",
        "tags.delete_dialog.title": "删除标签",
        "tags.delete_dialog.body": (
            "确定删除标签“{name}”吗？这会移除所有文章上的该标签，"
            "但不会删除文章。"
        ),
        "summary.title": "Summary",
        "summary.expand": "⌄ Summary",
        "summary.collapse": "⌃ Summary",
        "summary.hide_panel": "隐藏",
        "summary.hide_panel_tooltip": (
            "隐藏摘要面板；可通过 Reader 工具栏或 Ctrl+Shift+S 恢复"
        ),
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
        "summary.generate_tooltip.no_article": "请先选择一篇文章。",
        "summary.generate_tooltip.configure": "点击打开 AI 设置。",
        "summary.generate_tooltip.ready": "在后台为当前文章生成摘要。",
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
        "translation.expand": "⌄ Translation",
        "translation.collapse": "⌃ Translation",
        "translation.target_language": "目标语言：",
        "translation.language.zh_cn": "简体中文",
        "translation.language.en_us": "英文",
        "translation.custom_prompt": "自定义 Prompt：",
        "translation.custom_prompt_placeholder": (
            "可选；留空时使用默认翻译 Prompt"
        ),
        "translation.configure_ai": "AI 设置",
        "translation.original": "原文",
        "translation.translated": "译文",
        "translation.result_location": (
            "翻译结果会直接写入 Reader 正文，按“原文段落 → 对应译文”交替显示。"
        ),
        "translation.generate": "开始翻译",
        "translation.regenerate": "重新翻译",
        "translation.generate_tooltip.no_article": "请先选择一篇文章。",
        "translation.generate_tooltip.configure": "点击打开 AI 设置。",
        "translation.generate_tooltip.ready": (
            "在后台翻译当前文章并保留原文。"
        ),
        "translation.generated_at": "生成时间：{time}",
        "translation.status.no_article": "选择一篇文章后可以开始翻译。",
        "translation.status.unavailable": (
            "翻译服务尚不可用，请检查 AI Provider 设置。"
        ),
        "translation.status.ready": (
            "只有主动点击翻译后，文章内容才会发送给已配置的 Provider。"
        ),
        "translation.status.running": (
            "正在后台翻译，文章正文和已有原文仍可阅读……"
        ),
        "translation.status.completed": (
            "翻译已完成，Reader 已切换到双语对照。"
        ),
        "translation.status.partial": (
            "部分段落翻译失败；Reader 中的所有原文仍完整保留。"
        ),
        "translation.status.failed": "翻译失败；Reader 中的原文仍可阅读。",
        "translation.status.storage_warning": (
            "翻译已生成，但未能保存到本地。"
        ),
        "translation.paragraph.original_heading": "原文 · 段落 {number}",
        "translation.paragraph.translated_heading": "译文",
        "translation.paragraph.translated": "段落 {number}：已翻译",
        "translation.paragraph.partial": (
            "段落 {number}：部分翻译，失败分段的原文仍保留"
        ),
        "translation.paragraph.failed": "段落 {number}：{error}",
        "translation.paragraph.unavailable": "译文暂不可用",
        "translation.error.invalid_input": (
            "当前文章没有可用于翻译的正文；原文未受影响。"
        ),
        "translation.error.provider_not_configured": (
            "请先配置 AI Provider；原文仍可阅读。"
        ),
        "translation.error.provider_failure": (
            "Provider 翻译失败；原文仍可阅读。"
        ),
        "translation.error.empty_response": (
            "Provider 没有返回译文；原文仍可阅读。"
        ),
        "translation.error.wrong_language": (
            "Provider 未按目标语言返回译文；已丢弃错误内容，原文仍可阅读。"
        ),
        "translation.error.incomplete_response": (
            "Provider 未完整翻译当前段落；已丢弃不完整译文，原文仍可阅读。"
        ),
        "translation.error.load_failed": (
            "本地翻译读取失败，可以重新翻译。"
        ),
        "translation.error.unexpected": (
            "翻译操作失败，文章正文和原文未受影响。"
        ),
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
        "action.star": "Star",
        "action.unstar": "Unstar",
        "action.preferences": "Preferences",
        "action.ai_settings": "AI Settings",
        "action.toggle_tags_panel": "Tags Panel",
        "action.toggle_summary_panel": "Summary Panel",
        "action.toggle_translation_panel": "Translation Settings",
        "action.shortcuts": "Shortcuts",
        "action.exit": "Exit",
        "action.about": "About Mercury",
        "toolbar.main": "Main Toolbar",
        "sidebar.title": "Feeds",
        "sidebar.tab.feeds": "Feeds",
        "sidebar.tab.tags": "Tags",
        "sidebar.feed_detail": "{count} unread",
        "sidebar.all_feeds": "All Feeds",
        "sidebar.starred": "Starred",
        "sidebar.starred_detail": "{count}",
        "sidebar.footer": "Feeds: {feeds} · Unread: {unread}",
        "article_list.title": "Entries",
        "article_list.starred_title": "Starred",
        "article_list.tags_title": "Tags: {tags}",
        "article_list.unread_filter": "Unread",
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
        "reader.summary_toggle": "Summary",
        "reader.summary_toggle_tooltip": (
            "Show or hide the Summary panel (Ctrl+Shift+S)"
        ),
        "reader.translation_toggle": "Translation Settings",
        "reader.translation_toggle_tooltip": (
            "Show or hide translation settings inside Reader (Ctrl+Shift+T)"
        ),
        "reader.translation_view.bilingual": "Bilingual",
        "reader.translation_view.original": "Original only",
        "reader.translation_view.available_tooltip": (
            "Switch between original-only and paragraph bilingual reading"
        ),
        "reader.translation_view.unavailable_tooltip": (
            "Generate a translation for this article first"
        ),
        "reader.status.bilingual": "Showing paragraph bilingual reading",
        "reader.tags_toggle": "Tags",
        "reader.tags_toggle_tooltip": (
            "Show or hide the tag editor for the current article"
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
        "ai_settings.preset": "Configuration template:",
        "ai_settings.preset.custom": "Custom (OpenAI-compatible)",
        "ai_settings.preset.custom_description": (
            "The Base URL and model remain editable for any compatible "
            "Chat Completions service."
        ),
        "ai_settings.preset.ollama_qwen25_7b": (
            "Local Qwen2.5 7B (Ollama, recommended for translation)"
        ),
        "ai_settings.preset.ollama_qwen25_7b_description": (
            "Recommended for Chinese-English translation. There is no API "
            "cost; content is sent only to 127.0.0.1 and no API key is "
            "needed. Before use, run: ollama pull qwen2.5:7b-instruct"
        ),
        "ai_settings.preset.ollama_deepseek": (
            "Local DeepSeek (Ollama, no API cost)"
        ),
        "ai_settings.preset.ollama_deepseek_description": (
            "There is no API cost; content is sent only to 127.0.0.1 and "
            "no API key is needed. Install Ollama, then run: "
            "ollama pull deepseek-r1:1.5b"
        ),
        "ai_settings.preset.deepseek_api": (
            "Official DeepSeek API (usage billed)"
        ),
        "ai_settings.preset.deepseek_api_description": (
            "This is a paid cloud API and requires a DeepSeek API key and "
            "available balance; it is not the free option."
        ),
        "ai_settings.base_url": "Base URL:",
        "ai_settings.base_url_placeholder": (
            "Example: https://service-address/v1"
        ),
        "ai_settings.base_url_tooltip": (
            "Enter the Chat Completions API root; "
            "/chat/completions is appended automatically."
        ),
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
        "status.ai_settings_saved": "AI Provider settings saved locally.",
        "status.ai_settings_storage_failed": (
            "AI Provider settings could not be saved locally; "
            "existing reading features are unaffected."
        ),
        "status.add_feed_started": "Adding feed...",
        "status.import_opml_started": "Importing OPML...",
        "status.refresh_started": "Refreshing feeds...",
        "status.article_starred": "Entry starred",
        "status.article_unstarred": "Entry unstarred",
        "status.star_failed": (
            "The starred state could not be updated. "
            "The previous state was kept."
        ),
        "status.tags_added": "Tags added to the article.",
        "status.tag_assigned": "Tag added to the article.",
        "status.tag_removed": "Tag removed from the article.",
        "status.tag_renamed": "Tag renamed.",
        "status.tag_deleted": "Tag deleted.",
        "status.tag_failed": (
            "Local tags could not be updated. Reading remains available."
        ),
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
        "shortcuts.title": "Keyboard Shortcuts",
        "shortcuts.description": (
            "Keyboard shortcuts available on the current page and what they do."
        ),
        "shortcuts.key_header": "Shortcut",
        "shortcuts.function_header": "Function",
        "shortcuts.show_help": "Open this shortcut reference",
        "shortcuts.open_settings": "Open Preferences",
        "shortcuts.toggle_summary": "Show or hide the Summary panel",
        "shortcuts.toggle_translation": (
            "Show or hide Reader translation settings"
        ),
        "shortcuts.exit": "Exit Mercury",
        "shortcuts.close": "Close",
        "tags.title": "Tags",
        "tags.browser_hint": (
            "Browse local tags; edit article tags from the Reader."
        ),
        "tags.input_placeholder": "Type tags (comma-separated)",
        "tags.add": "Add",
        "tags.close": "Close tag editor",
        "tags.existing": "Existing",
        "tags.empty": "No tags yet. Create one for this article.",
        "tags.no_article": "Select an article to edit its tags.",
        "tags.filter_clear": "Clear tag filter",
        "tags.rename": "Rename",
        "tags.delete": "Delete",
        "tags.rename_dialog.title": "Rename Tag",
        "tags.rename_dialog.label": "New name:",
        "tags.delete_dialog.title": "Delete Tag",
        "tags.delete_dialog.body": (
            'Delete the tag "{name}"? It will be removed from every '
            "article, but no articles will be deleted."
        ),
        "summary.title": "Summary",
        "summary.expand": "⌄ Summary",
        "summary.collapse": "⌃ Summary",
        "summary.hide_panel": "Hide",
        "summary.hide_panel_tooltip": (
            "Hide the Summary panel; restore it from the Reader toolbar "
            "or with Ctrl+Shift+S"
        ),
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
        "summary.generate_tooltip.no_article": "Select an article first.",
        "summary.generate_tooltip.configure": "Open AI settings.",
        "summary.generate_tooltip.ready": (
            "Generate a summary for the current article in the background."
        ),
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
        "translation.expand": "⌄ Translation",
        "translation.collapse": "⌃ Translation",
        "translation.target_language": "Target language:",
        "translation.language.zh_cn": "Simplified Chinese",
        "translation.language.en_us": "English",
        "translation.custom_prompt": "Custom prompt:",
        "translation.custom_prompt_placeholder": (
            "Optional; leave empty to use the default translation prompt"
        ),
        "translation.configure_ai": "AI Settings",
        "translation.original": "Original",
        "translation.translated": "Translation",
        "translation.result_location": (
            "Translations are rendered directly in Reader as alternating "
            "original and translated paragraphs."
        ),
        "translation.generate": "Translate",
        "translation.regenerate": "Translate Again",
        "translation.generate_tooltip.no_article": "Select an article first.",
        "translation.generate_tooltip.configure": "Open AI settings.",
        "translation.generate_tooltip.ready": (
            "Translate the current article in the background while retaining "
            "the original."
        ),
        "translation.generated_at": "Generated: {time}",
        "translation.status.no_article": (
            "Select an article to start translation."
        ),
        "translation.status.unavailable": (
            "The translation service is unavailable; check AI Provider settings."
        ),
        "translation.status.ready": (
            "Article content is sent only after you explicitly start translation."
        ),
        "translation.status.running": (
            "Translating in the background; the article and existing originals "
            "remain readable…"
        ),
        "translation.status.completed": (
            "Translation completed; Reader is now showing bilingual text."
        ),
        "translation.status.partial": (
            "Some paragraphs failed; every original remains in Reader."
        ),
        "translation.status.failed": (
            "Translation failed; the original remains readable in Reader."
        ),
        "translation.status.storage_warning": (
            "Translation generated but could not be saved locally."
        ),
        "translation.paragraph.original_heading": (
            "Original · Paragraph {number}"
        ),
        "translation.paragraph.translated_heading": "Translation",
        "translation.paragraph.translated": (
            "Paragraph {number}: translated"
        ),
        "translation.paragraph.partial": (
            "Paragraph {number}: partially translated; originals for failed "
            "segments are retained"
        ),
        "translation.paragraph.failed": "Paragraph {number}: {error}",
        "translation.paragraph.unavailable": "Translation unavailable",
        "translation.error.invalid_input": (
            "This article has no readable content to translate; the original "
            "was not affected."
        ),
        "translation.error.provider_not_configured": (
            "Configure an AI Provider first; the original remains readable."
        ),
        "translation.error.provider_failure": (
            "Provider translation failed; the original remains readable."
        ),
        "translation.error.empty_response": (
            "The Provider returned no translation; the original remains readable."
        ),
        "translation.error.wrong_language": (
            "The Provider did not use the target language; the invalid output "
            "was discarded and the original remains readable."
        ),
        "translation.error.incomplete_response": (
            "The Provider did not translate the complete paragraph; the "
            "incomplete output was discarded and the original remains readable."
        ),
        "translation.error.load_failed": (
            "The local translation could not be loaded; you can translate again."
        ),
        "translation.error.unexpected": (
            "The translation action failed; the article and originals were not "
            "affected."
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
