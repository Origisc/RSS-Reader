# Agents 独立 Provider 设置界面（成员 B）

## 本次范围

- 在“设置”菜单中提供独立的“Agents 设置”页面。
- 左侧分别选择 Summary Agent、Translation Agent 和 Tag Agent；三者可使用
  不同 Base URL、模型、API Key 和超时，也可单独禁用。
- 支持填写 Provider 中立的 Base URL、模型、API Key 和超时时间。
- 提供可编辑配置模板：自定义、本地 Ollama Qwen2.5 7B、本地 Ollama
  DeepSeek、DeepSeek 官方 API。
- API Key 使用密码模式显示，不写入状态栏、异常文本或调试输出。
- 提供连接测试入口，并通过注入的连接测试器调用 Provider 适配层。
- 明确提示：只有用户主动触发摘要、翻译等 AI 功能时，文章内容才会发送给已配置的 Provider。

## 架构边界

Agents 设置窗口只负责表单、校验结果展示和用户交互，不直接实现网络协议或
绑定具体厂商。主窗口为三个 Agent 分别注入 `ProviderConfigStore` 和
`ConnectionTester`。

配置模板只是 UI 填表辅助，不改变统一 Provider 协议：用户修改模板给出的
Base URL 或模型后，界面会自动切回“自定义”。切换到另一服务模板时会清除
原 API Key，避免把一个服务的凭据误发给另一个服务。

“本地 Qwen2.5 7B（Ollama）”模板使用
`http://127.0.0.1:11434/v1` 和 `qwen2.5:7b-instruct`，不需要 API
Key，推荐用于中英翻译。使用前执行
`ollama pull qwen2.5:7b-instruct` 下载本地模型。

“本地 DeepSeek（Ollama）”模板使用
`http://127.0.0.1:11434/v1` 和 `deepseek-r1:1.5b`，不需要 API Key，
没有 API 调用费用，但需要用户自行安装 Ollama 并下载约 1.1 GB 的本地模型。
DeepSeek 官方云 API 是按量计费服务，界面明确标注为非免费方案。

正式应用为三个 Agent 分别注入厂商中立的
`HTTPChatCompletionsProvider`。连接测试使用当前 Agent 页面填写的配置；
保存后，摘要、翻译和标签建议会在用户主动点击时通过各自 Provider 发送
请求。自动测试使用 Mock 或内存 HTTP transport，全程不依赖真实网络或真实
API Key。

配置继续通过可替换的 `ProviderConfigStore` 保存。自动测试使用内存实现；
正式应用使用三个带 profile 的 `SQLiteProviderConfigStore` 写入现有本地
`database.db`，重启后会分别恢复各 Agent 的 Base URL、模型、可选 API Key
和超时。升级时旧的共享配置只迁移一次，初始复制给三个 Agent，之后互不
覆盖。数据库文件被 Git 忽略，Mercury 不会主动同步或上传这些配置。保存
失败时显示可翻译提示，基础阅读不受影响。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ai_settings tests.test_ai_persistence tests.test_http_llm_provider tests.test_ai_provider_integration tests.test_i18n tests.test_theme -v
```

验收点：

1. 未配置 Provider 时主界面仍加载三栏阅读数据。
2. API Key 输入框为密码模式。
3. Mock Provider 连接测试成功。
4. Summary、Translation、Tag 的连接测试和生成分别使用各自最新配置。
5. 失败信息即使意外包含 API Key，也会在 UI 中被遮盖。
6. 本地 Qwen2.5 7B 与 DeepSeek 模板使用回环地址、不保留其他服务的 API
   Key；手动修改 Base URL 或模型后恢复为自定义模板。
7. 三个 profile 使用不同模型时，关闭并重新创建配置 Store 后仍分别恢复；
   清除其中一个不会影响另外两个。
8. 旧共享配置升级后会复制给三个 Agent，迁移只执行一次。
