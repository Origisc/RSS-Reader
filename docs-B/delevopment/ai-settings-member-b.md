# AI Provider 设置界面（成员 B）

## 本次范围

- 在“设置”菜单中新增独立的“AI 设置”入口。
- 支持填写 Provider 中立的 Base URL、模型、API Key 和超时时间。
- API Key 使用密码模式显示，不写入状态栏、异常文本或调试输出。
- 提供连接测试入口，并通过注入的连接测试器调用 Provider 适配层。
- 明确提示：只有用户主动触发摘要、翻译等 AI 功能时，文章内容才会发送给已配置的 Provider。

## 架构边界

AI 设置窗口只负责表单、校验结果展示和用户交互，不直接实现网络协议或绑定具体厂商。主窗口通过 `ProviderConfigStore` 保存配置，通过 `ConnectionTester` 注入连接测试行为。

当前正式应用未接入真实 Provider 适配器，因此连接测试会明确显示“尚未发送到网络”，不会用 Mock 结果伪装真实连接。自动测试显式注入 `MockLLMProvider`，全程不依赖网络或真实 API Key。

配置当前使用可替换的内存存储；后续由本地 settings repository 实现并注入 `ProviderConfigStore` 后，可获得跨进程持久化，不需要修改 UI。

## 独立验证

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ai_settings tests.test_i18n tests.test_theme tests.test_llm_provider -v
```

验收点：

1. 未配置 Provider 时主界面仍加载三栏阅读数据。
2. API Key 输入框为密码模式。
3. Mock Provider 连接测试成功。
4. 无测试适配器时不会发起或伪装网络连接。
5. 失败信息即使意外包含 API Key，也会在 UI 中被遮盖。
