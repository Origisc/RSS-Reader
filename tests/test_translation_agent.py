import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.agents import (
    InMemoryTranslationResultStore,
    TranslationAgent,
    TranslationOptions,
    TranslationSource,
    clean_translation_response,
    extract_translation_paragraphs,
    segment_translation_text,
    translation_appears_complete,
    translation_matches_target_language,
    translation_validation_error,
)
from mercury.domain import (
    TranslationErrorCode,
    TranslationParagraphStatus,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.llm import (
    LLMProviderError,
    MockLLMProvider,
    ProviderConfig,
)


TEST_TIME = datetime(2026, 7, 19, 9, 0, tzinfo=UTC)


def configured_provider(**kwargs) -> MockLLMProvider:
    return MockLLMProvider(
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="user-selected-translation-model",
            api_key="translation-test-secret",
        ),
        **kwargs,
    )


def requested_text(request) -> str:
    return request.prompt.split("Text to translate:\n", 1)[1]


class TranslationTextProcessingTest(unittest.TestCase):
    def test_extracts_markdown_paragraphs_in_order(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.CLEANED_MARKDOWN,
            "First paragraph.\n\nSecond paragraph.\ncontinued\n\nThird.",
        )

        self.assertEqual(
            paragraphs,
            (
                "First paragraph.",
                "Second paragraph.\ncontinued",
                "Third.",
            ),
        )

    def test_extracts_html_blocks_and_ignores_script_content(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.CLEANED_HTML,
            (
                "<h2>Heading stays in Reader</h2>"
                "<p>First <strong>bold</strong>.</p>"
                "<script>private script text</script>"
                "<ul><li>Second item</li><li>Third item</li></ul>"
                "<ol><li>Fourth item</li><li>Fifth item</li></ol>"
            ),
        )

        self.assertEqual(
            paragraphs,
            (
                "First bold.",
                "Second item Third item",
                "Fourth item Fifth item",
            ),
        )

    def test_legacy_rss_br_fragments_fall_back_to_paragraphs(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.RAW_HTML,
            (
                "First line<br>continues here."
                "<br><br>"
                "Second paragraph."
                "<br /><br />"
                "Third paragraph."
            ),
        )

        self.assertEqual(
            paragraphs,
            (
                "First line continues here.",
                "Second paragraph.",
                "Third paragraph.",
            ),
        )

    def test_legacy_rss_body_is_not_hidden_by_appended_source_paragraph(
        self,
    ) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.RAW_HTML,
            (
                "First legacy paragraph.<br><br>"
                "Second legacy paragraph."
                '<p><a href="https://example.com/article">'
                "https://example.com/article"
                "</a></p>"
            ),
        )

        self.assertEqual(
            paragraphs,
            (
                "First legacy paragraph.",
                "Second legacy paragraph.",
                "https://example.com/article",
            ),
        )

    def test_legacy_rss_unicode_paragraph_breaks_are_supported(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.RAW_HTML,
            "First paragraph.\u2029Second paragraph.",
        )

        self.assertEqual(
            paragraphs,
            ("First paragraph.", "Second paragraph."),
        )

    def test_long_text_segments_preserve_order(self) -> None:
        text = "one two three four five six seven eight nine ten eleven"

        segments = segment_translation_text(text, max_chars=20)

        self.assertGreater(len(segments), 1)
        self.assertTrue(all(len(segment) <= 20 for segment in segments))
        self.assertEqual(" ".join(segments), text)

    def test_long_paragraph_prefers_sentence_boundary_before_however(
        self,
    ) -> None:
        first_sentence = (
            "Redis Cluster is nearing its first stable release after the "
            "Google group discussion [1]."
        )
        text = (
            f"{first_sentence} However, this second sentence contains "
            f"{'additional implementation details, ' * 12}"
            "and must also be translated."
        )

        segments = segment_translation_text(text, max_chars=300)

        self.assertEqual(segments[0], first_sentence)
        self.assertTrue(segments[1].startswith("However"))
        self.assertEqual(
            " ".join(segments),
            " ".join(text.split()),
        )

    def test_short_tail_is_merged_back_into_previous_segment(self) -> None:
        text = (
            "Some time ago I wrote about what I use in order to test Redis "
            "Cluster [4]. The most valuable tool I found so far is a simple "
            "consistency-test that is part of the redis-rb-cluster project "
            "[5] (a Ruby Redis Cluster client). Basically stress testing the "
            "system is as simple as keeping the consistency test running, "
            "while simulating different partitions, restarts, and other "
            "failures in the cluster."
        )

        segments = segment_translation_text(text, max_chars=160)

        self.assertEqual(len(segments), 3)
        self.assertTrue(segments[-1].endswith("the cluster."))
        self.assertGreater(len(segments[-1]), 40)
        self.assertEqual(" ".join(segments), text)


class TranslationAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = TranslationSource(
            article_id="article-1",
            title="Local-first article",
            raw_html="<p>Raw first.</p><p>Raw second.</p>",
            cleaned_html="<p>HTML first.</p><p>HTML second.</p>",
            cleaned_markdown="Markdown first.\n\nMarkdown second.",
        )

    def test_mock_provider_translates_paragraphs_in_order_and_saves(
        self,
    ) -> None:
        store = InMemoryTranslationResultStore()
        provider = configured_provider(
            responder=lambda request: f"译文：{requested_text(request)}"
        )
        agent = TranslationAgent(provider, store, clock=lambda: TEST_TIME)

        result = agent.translate(self.source)

        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertTrue(result.is_saved)
        self.assertEqual(result.generated_at, TEST_TIME)
        self.assertEqual(
            result.original_paragraphs,
            ("HTML first.", "HTML second."),
        )
        self.assertEqual(
            tuple(paragraph.index for paragraph in result.paragraphs),
            (0, 1),
        )
        self.assertEqual(
            tuple(paragraph.translated_text for paragraph in result.paragraphs),
            ("译文：HTML first.", "译文：HTML second."),
        )
        self.assertEqual(store.latest_for_article("article-1"), result)

    def test_cleaned_html_has_priority_for_reader_segment_alignment(
        self,
    ) -> None:
        provider = configured_provider(response_text="已翻译。")

        result = TranslationAgent(provider).translate(self.source)

        self.assertEqual(
            result.source_format,
            TranslationSourceFormat.CLEANED_HTML,
        )
        prompts = "\n".join(request.prompt for request in provider.requests)
        self.assertIn("HTML first", prompts)
        self.assertNotIn("Markdown first", prompts)
        self.assertNotIn("Raw first", prompts)

    def test_target_language_and_custom_prompt_enter_request(self) -> None:
        provider = configured_provider(response_text="translation")
        options = TranslationOptions(
            target_language="Japanese",
            custom_prompt="Translate technical terms consistently.",
        )

        TranslationAgent(provider).translate(self.source, options)

        request = provider.requests[0]
        self.assertIn("Target language: Japanese", request.prompt)
        self.assertIn(
            "Return only the translated text",
            request.system_prompt,
        )
        self.assertIn(
            "Additional user instructions:\n"
            "Translate technical terms consistently.",
            request.system_prompt,
        )
        self.assertEqual(request.temperature, 0)

    def test_leading_model_reasoning_is_not_mixed_into_translation(
        self,
    ) -> None:
        provider = configured_provider(
            response_text=(
                "<think>I should analyze the sentence first.</think>\n"
                "这是最终译文。"
            )
        )

        result = TranslationAgent(provider).translate(self.source)

        self.assertTrue(result.succeeded)
        self.assertTrue(
            all(
                paragraph.translated_text == "这是最终译文。"
                for paragraph in result.paragraphs
            )
        )
        self.assertNotIn(
            "analyze",
            " ".join(
                paragraph.translated_text
                for paragraph in result.paragraphs
            ),
        )

    def test_translation_response_keeps_non_reasoning_think_text(self) -> None:
        text = "译文中提到 <think> 是一个标签。"

        self.assertEqual(clean_translation_response(text), text)

    def test_retries_english_paraphrase_and_keeps_corrected_chinese(
        self,
    ) -> None:
        responses = iter(
            (
                "This is only an English paraphrase of the source paragraph.",
                "这是纠正后的中文译文。",
                "第二段中文译文。",
            )
        )
        provider = configured_provider(
            responder=lambda _request: next(responses)
        )

        result = TranslationAgent(provider).translate(self.source)

        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertEqual(
            result.paragraphs[0].translated_text,
            "这是纠正后的中文译文。",
        )
        self.assertEqual(len(provider.requests), 3)
        self.assertIn("CORRECTION REQUIRED", provider.requests[1].prompt)

    def test_discards_wrong_language_after_one_correction_attempt(
        self,
    ) -> None:
        provider = configured_provider(
            response_text="This is still an English copy, not Chinese."
        )

        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="wrong-language",
                title="Wrong language",
                raw_html="<p>A source paragraph requiring translation.</p>",
            )
        )

        paragraph = result.paragraphs[0]
        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(
            paragraph.error_code,
            TranslationErrorCode.WRONG_LANGUAGE,
        )
        self.assertFalse(paragraph.has_translation)
        self.assertEqual(len(provider.requests), 3)

    def test_retries_translation_that_omits_content_after_however(
        self,
    ) -> None:
        source_text = (
            "Redis Cluster is nearing its first stable release [1]. "
            "However, the remaining discussion explains several important "
            "implementation details and must not be omitted from translation."
        )
        complete_translation = (
            "Redis 集群即将迎来第一个稳定版本。"
            "然而，余下的讨论解释了若干重要的实现细节，"
            "这些内容也必须完整翻译，不能被省略。"
        )
        responses = iter(
            (
                "Redis 集群即将迎来第一个稳定版本。",
                complete_translation,
            )
        )
        provider = configured_provider(
            responder=lambda _request: next(responses)
        )

        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="incomplete-translation",
                title="Complete translation",
                raw_html=f"<p>{source_text}</p>",
            ),
            TranslationOptions(max_segment_chars=300),
        )

        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertEqual(
            result.paragraphs[0].translated_text,
            complete_translation,
        )
        self.assertEqual(len(provider.requests), 2)
        self.assertIn("complete source segment", provider.requests[1].prompt)

    def test_discards_incomplete_translation_after_correction(self) -> None:
        source_text = (
            "The first clause introduces the topic. However, the rest of "
            "this deliberately long source contains essential details that "
            "cannot be omitted from a faithful translation result."
        )
        provider = configured_provider(
            response_text="第一句已经翻译。"
        )

        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="still-incomplete",
                title="Incomplete translation",
                raw_html=f"<p>{source_text}</p>",
            ),
            TranslationOptions(max_segment_chars=300),
        )

        paragraph = result.paragraphs[0]
        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(
            paragraph.error_code,
            TranslationErrorCode.INCOMPLETE_RESPONSE,
        )
        self.assertFalse(paragraph.has_translation)
        self.assertEqual(len(provider.requests), 3)

    def test_failed_subsegment_recovers_with_full_paragraph_context(
        self,
    ) -> None:
        source_text = (
            "Some time ago I wrote about what I use in order to test Redis "
            "Cluster [4]. The most valuable tool I found so far is a simple "
            "consistency-test that is part of the redis-rb-cluster project "
            "[5] (a Ruby Redis Cluster client). Basically stress testing the "
            "system is as simple as keeping the consistency test running, "
            "while simulating different partitions, restarts, and other "
            "failures in the cluster."
        )
        recovered_translation = (
            "不久前，我写过用于测试 Redis 集群的工具。"
            "目前最有价值的是 redis-rb-cluster 项目中的一致性测试，"
            "它使用 Ruby Redis 集群客户端。压力测试只需持续运行一致性"
            "测试，同时模拟不同的网络分区、重启以及集群中的其他故障。"
        )

        def responder(request):
            text = requested_text(request)
            if text == source_text:
                return recovered_translation
            if "most valuable tool" in text:
                return text
            return "这是对应短片段的中文译文。"

        provider = configured_provider(responder=responder)
        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="paragraph-recovery",
                title="Redis recovery",
                raw_html=f"<p>{source_text}</p>",
            )
        )

        paragraph = result.paragraphs[0]
        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertEqual(
            paragraph.status,
            TranslationParagraphStatus.TRANSLATED,
        )
        self.assertEqual(paragraph.translated_text, recovered_translation)
        self.assertEqual(paragraph.segment_count, 1)
        self.assertTrue(
            any(
                requested_text(request) == source_text
                for request in provider.requests
            )
        )

    def test_target_language_validation_distinguishes_chinese_from_english(
        self,
    ) -> None:
        source = "A sufficiently descriptive English source paragraph."

        self.assertTrue(
            translation_matches_target_language(
                "这是对应的中文译文。",
                "Simplified Chinese",
                source,
            )
        )
        self.assertFalse(
            translation_matches_target_language(
                "This is merely an English rewrite.",
                "Simplified Chinese",
                source,
            )
        )
        self.assertFalse(
            translation_appears_complete(
                "只翻译了开头。",
                "Simplified Chinese",
                source * 4,
            )
        )
        self.assertEqual(
            translation_validation_error(
                "在本文的第二段，翻译为简体中文时应准确传达原意。",
                "Simplified Chinese",
                source,
            ),
            TranslationErrorCode.INCOMPLETE_RESPONSE,
        )

    def test_long_paragraph_is_translated_in_multiple_segments(self) -> None:
        long_text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron."
        )
        source = TranslationSource(
            article_id="long",
            title="Long article",
            raw_html="",
            cleaned_markdown=long_text,
        )
        provider = configured_provider(
            response_text="对应中文译文。"
        )

        result = TranslationAgent(provider).translate(
            source,
            TranslationOptions(max_segment_chars=24),
        )

        paragraph = result.paragraphs[0]
        self.assertGreater(paragraph.segment_count, 1)
        self.assertEqual(
            paragraph.segment_count,
            paragraph.translated_segment_count,
        )
        self.assertEqual(len(provider.requests), paragraph.segment_count)
        self.assertEqual(
            paragraph.status,
            TranslationParagraphStatus.TRANSLATED,
        )
        self.assertEqual(paragraph.original_text, long_text)

    def test_one_paragraph_failure_keeps_original_and_continues(self) -> None:
        calls = 0

        def responder(request):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise LLMProviderError("second paragraph fixture failure")
            return f"第{calls}段中文译文。"

        provider = configured_provider(responder=responder)
        source = TranslationSource(
            article_id="partial",
            title="Partial translation",
            raw_html="",
            cleaned_markdown="First.\n\nSecond.\n\nThird.",
        )

        result = TranslationAgent(provider).translate(source)

        self.assertEqual(result.status, TranslationStatus.PARTIAL)
        self.assertEqual(
            result.original_paragraphs,
            ("First.", "Second.", "Third."),
        )
        self.assertEqual(
            result.paragraphs[1].status,
            TranslationParagraphStatus.FAILED,
        )
        self.assertEqual(result.paragraphs[1].original_text, "Second.")
        self.assertFalse(result.paragraphs[1].has_translation)
        self.assertEqual(result.paragraphs[2].translated_text, "第3段中文译文。")
        self.assertEqual(len(provider.requests), 3)

    def test_one_long_paragraph_segment_failure_keeps_full_original(self) -> None:
        calls = 0

        def responder(request):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise LLMProviderError("middle segment fixture failure")
            return f"第{calls}个分段译文。"

        original = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron."
        )
        provider = configured_provider(responder=responder)
        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="partial-segment",
                title="Partial segment",
                raw_html="",
                cleaned_markdown=original,
            ),
            TranslationOptions(max_segment_chars=24),
        )

        paragraph = result.paragraphs[0]
        self.assertEqual(result.status, TranslationStatus.PARTIAL)
        self.assertEqual(
            paragraph.status,
            TranslationParagraphStatus.PARTIAL,
        )
        self.assertEqual(paragraph.original_text, original)
        self.assertEqual(
            paragraph.translated_segment_count,
            paragraph.segment_count - 1,
        )
        self.assertEqual(len(provider.requests), paragraph.segment_count)

    def test_empty_segment_response_does_not_drop_later_paragraphs(self) -> None:
        def responder(request):
            text = requested_text(request)
            return "" if text == "Two." else "有效的中文译文。"

        provider = configured_provider(responder=responder)
        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="empty-segment",
                title="Empty segment",
                raw_html="",
                cleaned_markdown="One.\n\nTwo.\n\nThree.",
            )
        )

        self.assertEqual(
            result.paragraphs[1].error_code,
            TranslationErrorCode.EMPTY_RESPONSE,
        )
        self.assertEqual(
            result.paragraphs[2].translated_text,
            "有效的中文译文。",
        )
        self.assertEqual(
            len(
                [
                    request
                    for request in provider.requests
                    if requested_text(request) == "Two."
                ]
            ),
            3,
        )
        self.assertEqual(len(provider.requests), 5)

    def test_unconfigured_provider_returns_all_originals_without_call(self) -> None:
        provider = MockLLMProvider(response_text="must not be used")

        result = TranslationAgent(provider).translate(self.source)

        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(
            result.error_code,
            TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
        )
        self.assertEqual(
            result.original_paragraphs,
            ("HTML first.", "HTML second."),
        )
        self.assertTrue(
            all(
                paragraph.status is TranslationParagraphStatus.FAILED
                for paragraph in result.paragraphs
            )
        )
        self.assertEqual(provider.requests, ())

    def test_provider_error_redacts_api_key(self) -> None:
        secret = "translation-test-secret"
        provider = configured_provider(
            failure_message=f"Credential {secret} rejected"
        )

        result = TranslationAgent(provider).translate(self.source)

        self.assertNotIn(secret, result.paragraphs[0].error_message)
        self.assertIn("••••", result.paragraphs[0].error_message)
        self.assertEqual(
            result.original_paragraphs,
            ("HTML first.", "HTML second."),
        )

    def test_storage_failure_keeps_translation_available(self) -> None:
        class FailingStore:
            def save(self, result) -> None:
                raise OSError("local fixture unavailable")

            def latest_for_article(self, article_id: str):
                return None

        result = TranslationAgent(
            configured_provider(response_text="仍然可以阅读。"),
            FailingStore(),
        ).translate(self.source)

        self.assertTrue(result.has_translations)
        self.assertFalse(result.is_saved)
        self.assertEqual(
            result.storage_error_code,
            TranslationErrorCode.STORAGE_FAILURE,
        )
        self.assertIn("could not be saved", result.storage_error_message)

    def test_missing_content_returns_failure_without_provider_call(self) -> None:
        provider = configured_provider(response_text="must not be used")
        source = TranslationSource(
            article_id="empty",
            title="Empty",
            raw_html="  ",
        )

        result = TranslationAgent(provider).translate(source)

        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(result.error_code, TranslationErrorCode.INVALID_INPUT)
        self.assertEqual(result.paragraphs, ())
        self.assertEqual(provider.requests, ())

    def test_legacy_rss_br_article_translates_each_paragraph(self) -> None:
        provider = configured_provider(
            response_text="对应的中文译文。"
        )
        progress_results = []
        source = TranslationSource(
            article_id="legacy-rss",
            title="Legacy RSS fragment",
            raw_html=(
                "First paragraph.<br><br>"
                "Second paragraph.<br><br>"
                "Third paragraph."
            ),
        )

        result = TranslationAgent(provider).translate(
            source,
            progress_callback=progress_results.append,
        )

        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertEqual(
            result.original_paragraphs,
            (
                "First paragraph.",
                "Second paragraph.",
                "Third paragraph.",
            ),
        )
        self.assertEqual(len(provider.requests), 3)
        self.assertEqual(len(progress_results), 3)
        self.assertTrue(
            all(
                len(progress.paragraphs) == 3
                for progress in progress_results
            )
        )
        self.assertEqual(
            [
                sum(
                    paragraph.has_translation
                    for paragraph in progress.paragraphs
                )
                for progress in progress_results
            ],
            [1, 2, 3],
        )


if __name__ == "__main__":
    unittest.main()
