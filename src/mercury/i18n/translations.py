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
        "action.delete_feeds": "批量删除所选 Feeds",
        "action.multi_select_feeds": "多选删除",
        "action.delete_selected_feeds": "删除所选（{count}）",
        "action.mark_read": "标记为已读",
        "action.mark_unread": "标记为未读",
        "action.star": "添加星标",
        "action.unstar": "取消星标",
        "action.preferences": "首选项",
        "action.ai_settings": "Agents 设置",
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
        "article_list.translate": "翻译标题",
        "article_list.translate.current": "翻译选中标题",
        "article_list.translate.all": "翻译当前列表全部标题",
        "article_list.translate.clear_current": "取消选中标题翻译",
        "article_list.translate.clear_all": "取消当前列表全部标题翻译",
        "article_list.translate.no_article": "请选中一个条目",
        "article_list.translate_all.confirm_title": "翻译全部标题",
        "article_list.translate_all.confirm_body": (
            "将当前 Entries 中 {count} 个尚无译文的标题发送给已配置的 "
            "Translation Provider，并按顺序翻译。是否继续？"
        ),
        "article_list.clear_all.confirm_title": "取消全部标题翻译",
        "article_list.clear_all.confirm_body": (
            "将清除当前 Entries 中 {count} 个标题的本地译文并恢复原标题。"
            "此操作不会调用 Provider。是否继续？"
        ),
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
        "reader.issue.link_only_loading": (
            "此 Feed 只提供了文章链接，Mercury 正在后台尝试加载网页正文。"
        ),
        "reader.issue.link_only_not_found": (
            "无法加载文章正文：目标网页返回 404，文章可能已被删除或链接已失效。"
            "你仍可使用下方链接在浏览器中确认。"
        ),
        "reader.issue.link_only_failed": (
            "无法加载文章正文：{error}。此 Feed 只提供了链接，"
            "你仍可使用下方链接在浏览器中打开。"
        ),
        "reader.issue.link_only_available": (
            "此 Feed 的原始内容只有链接；网页正文已经加载，"
            "可切换到 Cleaned HTML 或 Markdown 阅读。"
        ),
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
        "feed.add_dialog.label": "Feed URL 或本地文件路径：",
        "feed.delete_dialog.title": "删除 Feed",
        "feed.delete_dialog.body": (
            "确定删除订阅源“{title}”及其本地缓存文章吗？此操作不可撤销。"
        ),
        "feed.delete_many_dialog.title": "批量删除 Feeds",
        "feed.delete_many_dialog.body": (
            "确定删除以下 {count} 个订阅源及其全部本地缓存文章吗？"
            "此操作不可撤销。\n\n{titles}"
        ),
        "feed.delete_unavailable": (
            "删除服务未配置；当前不会修改本地订阅或文章。"
        ),
        "feed.delete_failed": "删除失败：订阅源不存在或本地数据库操作失败。",
        "feed.delete_many_failed": (
            "批量删除失败：所选订阅源已发生变化或本地数据库操作失败；"
            "本次没有删除任何订阅源。"
        ),
        "opml.import_dialog.title": "导入 OPML",
        "opml.import_dialog.filter": "OPML 文件 (*.opml *.xml);;所有文件 (*)",
        "feed.import_error.empty_source": (
            "未提供 Feed URL、本地 Feed 路径或 OPML 路径。"
        ),
        "feed.import_error.file_not_found": "找不到本地文件：{source}",
        "feed.import_error.not_a_file": "所选路径不是文件：{source}",
        "feed.import_error.file_read_failed": (
            "无法以 UTF-8 读取本地文件：{source}\n{detail}"
        ),
        "feed.import_error.unsupported_scheme": (
            "不支持此 Feed 来源：{source}\n"
            "请输入 HTTP(S) URL、相对文件路径或绝对文件路径。"
        ),
        "feed.import_error.network_failed": (
            "无法下载 Feed：{source}\n{detail}"
        ),
        "feed.import_error.invalid_feed": (
            "该来源不是有效的 RSS 或 Atom Feed：{source}\n{detail}"
        ),
        "feed.import_error.invalid_opml": (
            "该文件不是有效的 OPML 文档：{source}\n{detail}"
        ),
        "feed.import_error.opml_no_feeds": (
            "OPML 文档中没有包含 xmlUrl 的可导入 Feed：{source}"
        ),
        "feed.import_error.storage_failed": (
            "Feed 已读取，但无法保存到本地数据库：{source}\n{detail}"
        ),
        "settings.title": "设置",
        "settings.language": "界面语言：",
        "settings.theme": "界面主题：",
        "settings.reader_font_size": "正文字号：",
        "settings.reader_line_height": "正文行高：",
        "settings.reader_content_width": "正文宽度：",
        "settings.ok": "确定",
        "settings.cancel": "取消",
        "ai_settings.title": "AI Provider 设置",
        "agents_settings.title": "Agents",
        "agents_settings.properties": "Provider 属性",
        "agents_settings.enabled": "启用此 Agent",
        "agents_settings.save": "保存全部",
        "agents_settings.agent.summary": "Summary Agent",
        "agents_settings.agent.translation": "Translation Agent",
        "agents_settings.agent.tag": "Tag Agent",
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
        "ai_settings.invalid_config": "当前 Provider 配置无法使用。",
        "ai_settings.reason_prefix": "原因：{reason}",
        "ai_settings.validation.base_url_required": (
            "尚未填写 Base URL。"
        ),
        "ai_settings.validation.base_url_invalid": (
            "Base URL 必须是完整的 HTTP 或 HTTPS 地址。"
        ),
        "ai_settings.validation.model_required": "尚未填写模型名称。",
        "ai_settings.validation.timeout_out_of_range": (
            "超时时间必须在 {min} 到 {max} 秒之间。"
        ),
        "ai_settings.connection_unavailable": (
            "当前未接入 Provider 连接适配器；配置尚未发送到网络。"
        ),
        "ai_settings.connection_success": "连接测试成功。",
        "ai_settings.connection_failed": "连接测试失败。",
        "ai_settings.connection_reason.authentication": (
            "API Key 缺失、无效或已过期，请检查凭据。"
        ),
        "ai_settings.connection_reason.permission": (
            "Provider 已拒绝访问，请检查 API Key 权限、模型权限或账户状态。"
        ),
        "ai_settings.connection_reason.not_found": (
            "Provider 地址返回 404，请检查 Base URL、API 路径和模型名称。"
        ),
        "ai_settings.connection_reason.rate_limit": (
            "请求受到限流，或账户余额/配额不足，请稍后重试并检查账户。"
        ),
        "ai_settings.connection_reason.server": (
            "Provider 服务端暂时异常，请稍后重试。"
        ),
        "ai_settings.connection_reason.timeout": (
            "Provider 响应超时，请检查网络、VPN/代理、服务状态，"
            "或适当提高超时时间。"
        ),
        "ai_settings.connection_reason.proxy": (
            "无法通过代理连接，请检查 VPN/代理是否已连接以及代理配置。"
        ),
        "ai_settings.connection_reason.tls": (
            "HTTPS 证书校验失败，请检查系统时间、代理证书和 Provider 地址。"
        ),
        "ai_settings.connection_reason.invalid_url": (
            "Provider 地址无法解析，请检查 Base URL。"
        ),
        "ai_settings.connection_reason.incompatible_response": (
            "Provider 返回格式不兼容，请确认该地址支持 Chat Completions API。"
        ),
        "ai_settings.connection_reason.empty_response": (
            "Provider 已响应但没有返回内容，请检查模型名称和服务日志。"
        ),
        "ai_settings.connection_reason.local_unreachable": (
            "无法连接本地 Provider，请确认 Ollama/本地服务已启动，"
            "并检查 Base URL 和端口。"
        ),
        "ai_settings.connection_reason.remote_unreachable": (
            "无法连接远程 Provider；可能是网络、DNS、VPN/代理未连接，"
            "或 Base URL 填写错误。"
        ),
        "ai_settings.connection_reason.provider_message": (
            "Provider 返回：{message}"
        ),
        "ai_settings.connection_reason.internal": (
            "连接测试组件在收到 Provider 响应前发生错误；配置尚未保存。"
        ),
        "ai_settings.connection_reason.unknown": (
            "未收到可识别的 Provider 错误，请检查网络、服务状态和配置。"
        ),
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
        "status.ai_settings_load_failed.permission": (
            "无法读取 AI Provider 配置：没有本地数据目录的读取权限。"
        ),
        "status.ai_settings_load_failed.database": (
            "无法读取 AI Provider 配置：本地配置数据库不可用或已损坏。"
        ),
        "status.ai_settings_load_failed.unavailable": (
            "无法读取 AI Provider 配置：本地存储当前不可用。"
        ),
        "status.ai_settings_load_failed.unknown": (
            "无法读取 AI Provider 配置：发生未知的本地存储错误。"
        ),
        "status.ai_settings_save_failed.permission": (
            "AI Provider 配置无法保存到本地：没有本地数据目录的写入权限。"
        ),
        "status.ai_settings_save_failed.database": (
            "AI Provider 配置无法保存到本地：本地配置数据库写入失败。"
        ),
        "status.ai_settings_save_failed.unavailable": (
            "AI Provider 配置无法保存到本地：磁盘或本地存储当前不可用。"
        ),
        "status.ai_settings_save_failed.unknown": (
            "AI Provider 配置无法保存到本地：发生未知的本地存储错误。"
        ),
        "status.add_feed_started": "正在添加 Feed...",
        "status.import_opml_started": "正在导入 OPML...",
        "status.refresh_started": "正在刷新订阅源...",
        "status.article_starred": "已添加星标",
        "status.article_unstarred": "已取消星标",
        "status.star_failed": "无法更新星标，原状态已保留。",
        "status.translate_failed": "翻译失败：{message}",
        "status.title_translated": "标题翻译完成。",
        "status.title_translation_running": "正在依次翻译 {count} 个标题……",
        "status.title_translation_complete": (
            "标题翻译完成：成功 {success} 个，失败 {failed} 个。"
        ),
        "status.title_translation_none": "当前 Entries 中的标题均已有译文。",
        "status.title_translation_cleared": "已恢复原标题。",
        "status.title_translation_clear_complete": (
            "已恢复 {count} 个 Entries 原标题。"
        ),
        "status.title_translation_clear_none": (
            "当前 Entries 中没有可以取消的标题译文。"
        ),
        "status.title_translation_clear_failed": "无法清除本地标题译文。",
        "status.tags_added": "标签已添加到文章。",
        "status.tag_assigned": "标签已添加到文章。",
        "status.tag_removed": "已从文章移除标签。",
        "status.tag_renamed": "标签已重命名。",
        "status.tag_deleted": "标签已删除。",
        "status.tag_failed": "无法更新本地标签，原有阅读内容不受影响。",
        "status.delete_feed_started": "正在删除 Feed...",
        "status.delete_feed_finished": "已删除 Feed：{title}",
        "status.delete_feeds_started": "正在批量删除 {count} 个 Feeds...",
        "status.delete_feeds_finished": "已删除 {count} 个 Feeds。",
        "dialog.feature_failed.title": "操作失败",
        "dialog.feature_failed.unknown": "操作失败，但服务没有提供详细原因。",
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
        "tag_agent.title": "AI 标签建议",
        "tag_agent.custom_prompt_placeholder": (
            "可选：例如“使用简体中文标签”"
        ),
        "tag_agent.generate": "生成建议",
        "tag_agent.configure_ai": "AI 设置",
        "tag_agent.apply": "应用所选",
        "tag_agent.dismiss": "放弃建议",
        "tag_agent.status.no_article": "选择文章后可生成标签建议。",
        "tag_agent.status.unavailable": "Tag Agent 尚不可用，请检查 AI 设置。",
        "tag_agent.status.ready": (
            "点击生成后才会把当前文章发送给已配置的 Provider。"
        ),
        "tag_agent.status.running": "正在后台生成标签建议……",
        "tag_agent.status.generated": "请选择建议并点击“应用所选”。",
        "tag_agent.error.invalid_input": "当前文章没有可用于生成标签的正文。",
        "tag_agent.error.provider_not_configured": "请先配置 AI Provider。",
        "tag_agent.error.provider_failure": (
            "标签建议生成失败；手动标签和文章阅读不受影响。"
        ),
        "tag_agent.error.empty_response": "Provider 没有返回可用的标签建议。",
        "tag_agent.error.unexpected": (
            "标签建议操作失败；手动标签和文章阅读不受影响。"
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
        "summary.error.wrong_language": (
            "Provider 未使用所选摘要语言；已自动校正重试，请检查模型设置。"
        ),
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
        "translation.paragraph.translating": "正在翻译...",
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
        "action.delete_feeds": "Delete selected Feeds",
        "action.multi_select_feeds": "Select multiple",
        "action.delete_selected_feeds": "Delete selected ({count})",
        "action.mark_read": "Mark as read",
        "action.mark_unread": "Mark as unread",
        "action.star": "Star",
        "action.unstar": "Unstar",
        "action.preferences": "Preferences",
        "action.ai_settings": "Agents Settings",
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
        "article_list.translate": "Translate title",
        "article_list.translate.current": "Translate selected title",
        "article_list.translate.all": "Translate all titles in this list",
        "article_list.translate.clear_current": (
            "Remove selected title translation"
        ),
        "article_list.translate.clear_all": (
            "Remove all title translations in this list"
        ),
        "article_list.translate.no_article": "Please select an entry",
        "article_list.translate_all.confirm_title": "Translate all titles",
        "article_list.translate_all.confirm_body": (
            "Send the {count} untranslated titles currently shown in Entries "
            "to the configured Translation Provider and translate them "
            "sequentially?"
        ),
        "article_list.clear_all.confirm_title": (
            "Remove all title translations"
        ),
        "article_list.clear_all.confirm_body": (
            "Remove {count} locally stored title translations from the "
            "current Entries list and restore the original titles? "
            "This does not call the Provider."
        ),
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
        "reader.issue.link_only_loading": (
            "This Feed only provides an article link. Mercury is trying "
            "to load the webpage content in the background."
        ),
        "reader.issue.link_only_not_found": (
            "The article body could not be loaded because the webpage "
            "returned 404. It may have been removed or moved. You can "
            "still use the link below to check it in a browser."
        ),
        "reader.issue.link_only_failed": (
            "The article body could not be loaded: {error}. This Feed only "
            "provides a link, which you can still open in a browser."
        ),
        "reader.issue.link_only_available": (
            "The original Feed content only contains a link. The webpage "
            "body is available in Cleaned HTML or Markdown."
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
        "feed.add_dialog.label": "Feed URL or local file path:",
        "feed.delete_dialog.title": "Delete Feed",
        "feed.delete_dialog.body": (
            "Delete the feed “{title}” and its locally cached articles? "
            "This action cannot be undone."
        ),
        "feed.delete_many_dialog.title": "Delete multiple Feeds",
        "feed.delete_many_dialog.body": (
            "Delete these {count} feeds and all their locally cached "
            "articles? This action cannot be undone.\n\n{titles}"
        ),
        "feed.delete_unavailable": (
            "The deletion service is not configured. "
            "No local feeds or articles were changed."
        ),
        "feed.delete_failed": (
            "Deletion failed because the feed was not found or the local database operation failed."
        ),
        "feed.delete_many_failed": (
            "Batch deletion failed because the selected feeds changed or "
            "the local database operation failed. No feeds were deleted."
        ),
        "opml.import_dialog.title": "Import OPML",
        "opml.import_dialog.filter": "OPML files (*.opml *.xml);;All files (*)",
        "feed.import_error.empty_source": (
            "No Feed URL, local Feed path, or OPML path was provided."
        ),
        "feed.import_error.file_not_found": (
            "The local file was not found: {source}"
        ),
        "feed.import_error.not_a_file": (
            "The selected path is not a file: {source}"
        ),
        "feed.import_error.file_read_failed": (
            "The local file could not be read as UTF-8: {source}\n{detail}"
        ),
        "feed.import_error.unsupported_scheme": (
            "This Feed source is unsupported: {source}\n"
            "Enter an HTTP(S) URL, relative file path, or absolute file path."
        ),
        "feed.import_error.network_failed": (
            "The Feed could not be downloaded: {source}\n{detail}"
        ),
        "feed.import_error.invalid_feed": (
            "The source is not a valid RSS or Atom Feed: {source}\n{detail}"
        ),
        "feed.import_error.invalid_opml": (
            "The file is not a valid OPML document: {source}\n{detail}"
        ),
        "feed.import_error.opml_no_feeds": (
            "The OPML document has no importable Feed with an xmlUrl: "
            "{source}"
        ),
        "feed.import_error.storage_failed": (
            "The Feed was read but could not be saved locally: "
            "{source}\n{detail}"
        ),
        "settings.title": "Settings",
        "settings.language": "Interface language:",
        "settings.theme": "Interface theme:",
        "settings.reader_font_size": "Reader font size:",
        "settings.reader_line_height": "Reader line height:",
        "settings.reader_content_width": "Reader content width:",
        "settings.ok": "OK",
        "settings.cancel": "Cancel",
        "ai_settings.title": "AI Provider Settings",
        "agents_settings.title": "Agents",
        "agents_settings.properties": "Provider properties",
        "agents_settings.enabled": "Enable this Agent",
        "agents_settings.save": "Save all",
        "agents_settings.agent.summary": "Summary Agent",
        "agents_settings.agent.translation": "Translation Agent",
        "agents_settings.agent.tag": "Tag Agent",
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
            "The current Provider configuration cannot be used."
        ),
        "ai_settings.reason_prefix": "Reason: {reason}",
        "ai_settings.validation.base_url_required": (
            "Base URL has not been entered."
        ),
        "ai_settings.validation.base_url_invalid": (
            "Base URL must be a complete HTTP or HTTPS address."
        ),
        "ai_settings.validation.model_required": (
            "Model name has not been entered."
        ),
        "ai_settings.validation.timeout_out_of_range": (
            "Timeout must be between {min} and {max} seconds."
        ),
        "ai_settings.connection_unavailable": (
            "No Provider connection adapter is available; the configuration was not sent "
            "over the network."
        ),
        "ai_settings.connection_success": "Connection test succeeded.",
        "ai_settings.connection_failed": "Connection test failed.",
        "ai_settings.connection_reason.authentication": (
            "The API key is missing, invalid, or expired. Check the credential."
        ),
        "ai_settings.connection_reason.permission": (
            "The Provider denied access. Check API-key permissions, model "
            "access, and account status."
        ),
        "ai_settings.connection_reason.not_found": (
            "The Provider returned 404. Check the Base URL, API path, and "
            "model name."
        ),
        "ai_settings.connection_reason.rate_limit": (
            "The request was rate-limited, or the account has insufficient "
            "credit or quota. Check the account and retry later."
        ),
        "ai_settings.connection_reason.server": (
            "The Provider has a temporary server error. Retry later."
        ),
        "ai_settings.connection_reason.timeout": (
            "The Provider timed out. Check the network, VPN/proxy, and "
            "service status, or increase the timeout."
        ),
        "ai_settings.connection_reason.proxy": (
            "The proxy connection failed. Check whether the VPN/proxy is "
            "connected and configured correctly."
        ),
        "ai_settings.connection_reason.tls": (
            "HTTPS certificate validation failed. Check the system clock, "
            "proxy certificate, and Provider address."
        ),
        "ai_settings.connection_reason.invalid_url": (
            "The Provider address could not be parsed. Check the Base URL."
        ),
        "ai_settings.connection_reason.incompatible_response": (
            "The Provider response is incompatible. Confirm that the address "
            "supports the Chat Completions API."
        ),
        "ai_settings.connection_reason.empty_response": (
            "The Provider responded without content. Check the model name "
            "and service logs."
        ),
        "ai_settings.connection_reason.local_unreachable": (
            "The local Provider could not be reached. Confirm that Ollama or "
            "the local service is running, then check the Base URL and port."
        ),
        "ai_settings.connection_reason.remote_unreachable": (
            "The remote Provider could not be reached. Possible causes "
            "include network or DNS failure, a disconnected VPN/proxy, or "
            "an incorrect Base URL."
        ),
        "ai_settings.connection_reason.provider_message": (
            "Provider response: {message}"
        ),
        "ai_settings.connection_reason.internal": (
            "The connection-test component failed before a Provider response "
            "was received. The configuration was not saved."
        ),
        "ai_settings.connection_reason.unknown": (
            "No recognizable Provider error was received. Check the network, "
            "service status, and configuration."
        ),
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
        "status.ai_settings_load_failed.permission": (
            "AI Provider settings could not be read: the local data "
            "directory is not readable."
        ),
        "status.ai_settings_load_failed.database": (
            "AI Provider settings could not be read: the local configuration "
            "database is unavailable or damaged."
        ),
        "status.ai_settings_load_failed.unavailable": (
            "AI Provider settings could not be read: local storage is "
            "currently unavailable."
        ),
        "status.ai_settings_load_failed.unknown": (
            "AI Provider settings could not be read because of an unknown "
            "local storage error."
        ),
        "status.ai_settings_save_failed.permission": (
            "AI Provider settings could not be saved locally: the local data "
            "directory is not writable."
        ),
        "status.ai_settings_save_failed.database": (
            "AI Provider settings could not be saved locally: writing the "
            "local configuration database failed."
        ),
        "status.ai_settings_save_failed.unavailable": (
            "AI Provider settings could not be saved locally: the disk or "
            "local storage is currently unavailable."
        ),
        "status.ai_settings_save_failed.unknown": (
            "AI Provider settings could not be saved locally because of an "
            "unknown local storage error."
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
        "status.translate_failed": "Translation failed: {message}",
        "status.title_translated": "Title translation completed.",
        "status.title_translation_running": (
            "Translating {count} titles sequentially…"
        ),
        "status.title_translation_complete": (
            "Title translation completed: {success} succeeded and "
            "{failed} failed."
        ),
        "status.title_translation_none": (
            "Every title currently shown in Entries already has a translation."
        ),
        "status.title_translation_cleared": "The original title was restored.",
        "status.title_translation_clear_complete": (
            "Restored {count} original Entry titles."
        ),
        "status.title_translation_clear_none": (
            "There are no title translations to remove in the current Entries."
        ),
        "status.title_translation_clear_failed": (
            "The local title translation could not be removed."
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
        "status.delete_feeds_started": "Deleting {count} feeds...",
        "status.delete_feeds_finished": "Deleted {count} feeds.",
        "dialog.feature_failed.title": "Action Failed",
        "dialog.feature_failed.unknown": (
            "The action failed without a detailed service error."
        ),
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
        "tag_agent.title": "AI tag suggestions",
        "tag_agent.custom_prompt_placeholder": (
            'Optional, for example: "Use Simplified Chinese tags"'
        ),
        "tag_agent.generate": "Suggest tags",
        "tag_agent.configure_ai": "AI Settings",
        "tag_agent.apply": "Apply selected",
        "tag_agent.dismiss": "Dismiss",
        "tag_agent.status.no_article": (
            "Select an article to generate tag suggestions."
        ),
        "tag_agent.status.unavailable": (
            "Tag Agent is unavailable; check AI settings."
        ),
        "tag_agent.status.ready": (
            "The article is sent to the configured Provider only after "
            "you request suggestions."
        ),
        "tag_agent.status.running": "Generating tag suggestions…",
        "tag_agent.status.generated": (
            "Select suggestions, then choose Apply selected."
        ),
        "tag_agent.error.invalid_input": (
            "This article has no readable content for tag suggestions."
        ),
        "tag_agent.error.provider_not_configured": (
            "Configure an AI Provider first."
        ),
        "tag_agent.error.provider_failure": (
            "Tag suggestions failed; manual tags and reading are unaffected."
        ),
        "tag_agent.error.empty_response": (
            "The Provider returned no usable tag suggestions."
        ),
        "tag_agent.error.unexpected": (
            "Tag suggestions failed; manual tags and reading are unaffected."
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
        "summary.error.wrong_language": (
            "The Provider did not use the selected summary language after "
            "automatic correction attempts."
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
        "translation.paragraph.translating": "Translating...",
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
