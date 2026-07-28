import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.domain import (
    SummaryDetail,
    SummaryResult,
    SummarySourceFormat,
    TranslationErrorCode,
    TranslationParagraph,
    TranslationParagraphStatus,
    TranslationResult,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.llm import ProviderConfig, ProviderConfigError
from mercury.storage import (
    SQLiteProviderConfigStore,
    SQLiteSummaryResultStore,
    SQLiteTranslationResultStore,
)


TEST_TIME = datetime(2026, 7, 25, 8, 30, tzinfo=UTC)


class AIPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self._temporary_directory.name) / "mercury-test.db"
        )

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_provider_config_survives_store_recreation_and_can_clear(
        self,
    ) -> None:
        config = ProviderConfig(
            base_url="http://127.0.0.1:11434/v1",
            model="user-selected-model",
            api_key="local-test-secret",
            timeout_seconds=120.0,
        )
        SQLiteProviderConfigStore(self.database_path).save(config)

        restarted_store = SQLiteProviderConfigStore(self.database_path)

        self.assertEqual(restarted_store.load(), config)
        self.assertNotIn(
            config.api_key,
            repr(restarted_store.load()),
        )
        restarted_store.clear()
        self.assertIsNone(
            SQLiteProviderConfigStore(self.database_path).load()
        )

    def test_invalid_provider_config_is_not_persisted(self) -> None:
        store = SQLiteProviderConfigStore(self.database_path)

        with self.assertRaises(ProviderConfigError):
            store.save(ProviderConfig(base_url="invalid", model=""))

        self.assertIsNone(store.load())

    def test_agent_provider_profiles_are_independent_and_persistent(
        self,
    ) -> None:
        configs = {
            agent_id: ProviderConfig(
                base_url="http://127.0.0.1:8080/v1",
                model=f"{agent_id}-model",
                api_key=f"{agent_id}-secret",
            )
            for agent_id in ("summary", "translation", "tag")
        }
        for agent_id, config in configs.items():
            SQLiteProviderConfigStore(
                self.database_path,
                profile=agent_id,
            ).save(config)

        loaded = {
            agent_id: SQLiteProviderConfigStore(
                self.database_path,
                profile=agent_id,
            ).load()
            for agent_id in configs
        }

        self.assertEqual(loaded, configs)
        SQLiteProviderConfigStore(
            self.database_path,
            profile="tag",
        ).clear()
        self.assertIsNone(
            SQLiteProviderConfigStore(
                self.database_path,
                profile="tag",
            ).load()
        )
        self.assertEqual(
            SQLiteProviderConfigStore(
                self.database_path,
                profile="summary",
            ).load(),
            configs["summary"],
        )

    def test_legacy_single_provider_is_migrated_once_to_all_agents(
        self,
    ) -> None:
        legacy = ProviderConfig(
            base_url="http://127.0.0.1:11434/v1",
            model="legacy-model",
            api_key="legacy-secret",
            timeout_seconds=90.0,
        )
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute(
                """
                CREATE TABLE ai_provider_config (
                    singleton_id INTEGER PRIMARY KEY
                        CHECK (singleton_id = 1),
                    base_url TEXT NOT NULL,
                    model TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO ai_provider_config
                VALUES (1, ?, ?, ?, ?, ?)
                """,
                (
                    legacy.base_url,
                    legacy.model,
                    legacy.api_key,
                    legacy.timeout_seconds,
                    TEST_TIME.isoformat(),
                ),
            )
            connection.commit()

        self.assertEqual(
            {
                agent_id: SQLiteProviderConfigStore(
                    self.database_path,
                    profile=agent_id,
                ).load()
                for agent_id in ("summary", "translation", "tag")
            },
            {
                "summary": legacy,
                "translation": legacy,
                "tag": legacy,
            },
        )

        tag_store = SQLiteProviderConfigStore(
            self.database_path,
            profile="tag",
        )
        tag_store.clear()
        self.assertIsNone(
            SQLiteProviderConfigStore(
                self.database_path,
                profile="tag",
            ).load()
        )

    def test_summary_round_trip_preserves_unicode_and_metadata(self) -> None:
        result = SummaryResult(
            article_id="article-摘要",
            text="这是离线保存的摘要。",
            language="简体中文",
            detail_level=SummaryDetail.DETAILED,
            source_format=SummarySourceFormat.CLEANED_MARKDOWN,
            generated_at=TEST_TIME,
            provider_model="user-selected-model",
        )
        SQLiteSummaryResultStore(self.database_path).save(result)

        loaded = SQLiteSummaryResultStore(
            self.database_path
        ).latest_for_article(result.article_id)

        self.assertEqual(loaded, result)
        self.assertIsNone(
            SQLiteSummaryResultStore(
                self.database_path
            ).latest_for_article("missing")
        )

    def test_translation_round_trip_preserves_paragraph_alignment(
        self,
    ) -> None:
        result = TranslationResult(
            article_id="article-translation",
            target_language="Simplified Chinese",
            paragraphs=(
                TranslationParagraph(
                    index=0,
                    original_text="First paragraph.",
                    translated_text="第一段。",
                    status=TranslationParagraphStatus.TRANSLATED,
                    segment_count=1,
                    translated_segment_count=1,
                ),
                TranslationParagraph(
                    index=1,
                    original_text="Second paragraph stays readable.",
                    translated_text="",
                    status=TranslationParagraphStatus.FAILED,
                    segment_count=1,
                    translated_segment_count=0,
                    error_code=TranslationErrorCode.PROVIDER_FAILURE,
                    error_message="Translation failed.",
                ),
            ),
            source_format=TranslationSourceFormat.CLEANED_HTML,
            generated_at=TEST_TIME,
            provider_model="user-selected-model",
            status=TranslationStatus.PARTIAL,
            is_saved=True,
        )
        SQLiteTranslationResultStore(self.database_path).save(result)

        loaded = SQLiteTranslationResultStore(
            self.database_path
        ).latest_for_article(result.article_id)

        self.assertEqual(loaded, result)
        self.assertEqual(
            loaded.original_paragraphs,
            (
                "First paragraph.",
                "Second paragraph stays readable.",
            ),
        )

    def test_translation_save_rolls_back_header_when_paragraphs_fail(
        self,
    ) -> None:
        duplicated_index = TranslationResult(
            article_id="atomic-translation",
            target_language="Simplified Chinese",
            paragraphs=(
                TranslationParagraph(
                    index=0,
                    original_text="First.",
                    translated_text="第一段。",
                    status=TranslationParagraphStatus.TRANSLATED,
                    segment_count=1,
                    translated_segment_count=1,
                ),
                TranslationParagraph(
                    index=0,
                    original_text="Duplicate.",
                    translated_text="重复。",
                    status=TranslationParagraphStatus.TRANSLATED,
                    segment_count=1,
                    translated_segment_count=1,
                ),
            ),
            source_format=TranslationSourceFormat.CLEANED_HTML,
            generated_at=TEST_TIME,
            provider_model="model",
            status=TranslationStatus.COMPLETED,
            is_saved=True,
        )
        store = SQLiteTranslationResultStore(self.database_path)

        with self.assertRaises(sqlite3.IntegrityError):
            store.save(duplicated_index)

        self.assertIsNone(
            store.latest_for_article("atomic-translation")
        )

    def test_translation_history_is_bounded_and_cascades_paragraphs(
        self,
    ) -> None:
        store = SQLiteTranslationResultStore(self.database_path)
        for offset in range(25):
            store.save(
                TranslationResult(
                    article_id="bounded-history",
                    target_language="Simplified Chinese",
                    paragraphs=(
                        TranslationParagraph(
                            index=0,
                            original_text="Original.",
                            translated_text=f"译文 {offset}",
                            status=(
                                TranslationParagraphStatus.TRANSLATED
                            ),
                            segment_count=1,
                            translated_segment_count=1,
                        ),
                    ),
                    source_format=TranslationSourceFormat.CLEANED_HTML,
                    generated_at=TEST_TIME + timedelta(minutes=offset),
                    provider_model="model",
                    status=TranslationStatus.COMPLETED,
                    is_saved=True,
                )
            )

        with closing(sqlite3.connect(self.database_path)) as connection:
            result_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM ai_translation_results
                WHERE article_id = 'bounded-history'
                """
            ).fetchone()[0]
            paragraph_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM ai_translation_paragraphs
                """
            ).fetchone()[0]

        self.assertEqual(result_count, 20)
        self.assertEqual(paragraph_count, 20)
        self.assertEqual(
            store.latest_for_article(
                "bounded-history"
            ).paragraphs[0].translated_text,
            "译文 24",
        )

    def test_latest_result_is_loaded_after_multiple_generations(self) -> None:
        store = SQLiteSummaryResultStore(self.database_path)
        for offset, text in enumerate(("first", "second", "latest")):
            store.save(
                SummaryResult(
                    article_id="regenerated",
                    text=text,
                    language="English",
                    detail_level=SummaryDetail.STANDARD,
                    source_format=SummarySourceFormat.CLEANED_HTML,
                    generated_at=TEST_TIME + timedelta(minutes=offset),
                    provider_model="model",
                )
            )

        loaded = SQLiteSummaryResultStore(
            self.database_path
        ).latest_for_article("regenerated")

        self.assertEqual(loaded.text, "latest")

    def test_background_thread_writes_use_independent_connections(
        self,
    ) -> None:
        store = SQLiteSummaryResultStore(self.database_path)

        def save(index: int) -> None:
            store.save(
                SummaryResult(
                    article_id=f"thread-{index}",
                    text=f"summary-{index}",
                    language="English",
                    detail_level=SummaryDetail.BRIEF,
                    source_format=SummarySourceFormat.RAW_HTML,
                    generated_at=TEST_TIME,
                    provider_model="mock",
                )
            )

        with ThreadPoolExecutor(max_workers=4) as executor:
            tuple(executor.map(save, range(8)))

        self.assertEqual(
            [
                store.latest_for_article(f"thread-{index}").text
                for index in range(8)
            ],
            [f"summary-{index}" for index in range(8)],
        )

    def test_ai_tables_coexist_with_existing_reader_database(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute(
                "CREATE TABLE feeds (id INTEGER PRIMARY KEY, title TEXT)"
            )
            connection.execute(
                "INSERT INTO feeds (title) VALUES ('Local feed')"
            )
            connection.commit()

        SQLiteProviderConfigStore(self.database_path).save(
            ProviderConfig(
                base_url="http://127.0.0.1:11434/v1",
                model="local-model",
            )
        )

        with closing(sqlite3.connect(self.database_path)) as connection:
            feed_title = connection.execute(
                "SELECT title FROM feeds"
            ).fetchone()[0]

        self.assertEqual(feed_title, "Local feed")


if __name__ == "__main__":
    unittest.main()
