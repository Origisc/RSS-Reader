from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3

from mercury.domain import (
    SummaryDetail,
    SummaryErrorCode,
    SummaryResult,
    SummarySourceFormat,
    SummaryStatus,
    TranslationErrorCode,
    TranslationParagraph,
    TranslationParagraphStatus,
    TranslationResult,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.llm.config import ProviderConfig


_SQLITE_TIMEOUT_SECONDS = 10.0
_MAX_RESULTS_PER_ARTICLE = 20
AGENT_PROVIDER_IDS = ("summary", "translation", "tag")
_AGENT_CONFIG_MIGRATION = "agent-provider-config-v1"


class _SQLiteStore:
    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self._database_path,
            timeout=_SQLITE_TIMEOUT_SECONDS,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS ai_provider_config (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    base_url TEXT NOT NULL,
                    model TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_agent_provider_configs (
                    agent_id TEXT PRIMARY KEY,
                    base_url TEXT NOT NULL,
                    model TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_config_migrations (
                    migration_key TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_summary_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    detail_level TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    provider_model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    error_message TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS
                    idx_ai_summary_article_latest
                ON ai_summary_results(article_id, id DESC);

                CREATE TABLE IF NOT EXISTS ai_translation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    provider_model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_saved INTEGER NOT NULL,
                    error_code TEXT,
                    error_message TEXT NOT NULL,
                    storage_error_code TEXT,
                    storage_error_message TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS
                    idx_ai_translation_article_latest
                ON ai_translation_results(article_id, id DESC);

                CREATE TABLE IF NOT EXISTS ai_translation_paragraphs (
                    result_id INTEGER NOT NULL,
                    paragraph_index INTEGER NOT NULL,
                    original_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    segment_count INTEGER NOT NULL,
                    translated_segment_count INTEGER NOT NULL,
                    error_code TEXT,
                    error_message TEXT NOT NULL,
                    PRIMARY KEY (result_id, paragraph_index),
                    FOREIGN KEY(result_id)
                        REFERENCES ai_translation_results(id)
                        ON DELETE CASCADE
                );
                """
            )
            self._migrate_legacy_agent_configs(connection)

    @staticmethod
    def _migrate_legacy_agent_configs(
        connection: sqlite3.Connection,
    ) -> None:
        migrated = connection.execute(
            """
            SELECT 1
            FROM ai_config_migrations
            WHERE migration_key = ?
            """,
            (_AGENT_CONFIG_MIGRATION,),
        ).fetchone()
        if migrated is not None:
            return

        legacy = connection.execute(
            """
            SELECT base_url, model, api_key, timeout_seconds, updated_at
            FROM ai_provider_config
            WHERE singleton_id = 1
            """
        ).fetchone()
        if legacy is not None:
            connection.executemany(
                """
                INSERT OR IGNORE INTO ai_agent_provider_configs (
                    agent_id,
                    base_url,
                    model,
                    api_key,
                    timeout_seconds,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        agent_id,
                        legacy["base_url"],
                        legacy["model"],
                        legacy["api_key"],
                        legacy["timeout_seconds"],
                        legacy["updated_at"],
                    )
                    for agent_id in AGENT_PROVIDER_IDS
                ),
            )
        connection.execute(
            """
            INSERT INTO ai_config_migrations (migration_key, applied_at)
            VALUES (?, ?)
            """,
            (
                _AGENT_CONFIG_MIGRATION,
                datetime.now().astimezone().isoformat(),
            ),
        )


class SQLiteProviderConfigStore(_SQLiteStore):
    """Local provider configuration backed by Mercury's SQLite database."""

    def __init__(
        self,
        database_path: str | Path,
        profile: str = "default",
    ) -> None:
        normalized_profile = str(profile).strip().casefold()
        if (
            normalized_profile != "default"
            and normalized_profile not in AGENT_PROVIDER_IDS
        ):
            raise ValueError("Unsupported AI Provider profile.")
        self._profile = normalized_profile
        super().__init__(database_path)

    def load(self) -> ProviderConfig | None:
        if self._profile != "default":
            return self._load_agent_config()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT base_url, model, api_key, timeout_seconds
                FROM ai_provider_config
                WHERE singleton_id = 1
                """
            ).fetchone()

        if row is None:
            return None

        return ProviderConfig(
            base_url=row["base_url"],
            model=row["model"],
            api_key=row["api_key"],
            timeout_seconds=float(row["timeout_seconds"]),
        )

    def save(self, config: ProviderConfig) -> None:
        config.require_valid()
        if self._profile != "default":
            self._save_agent_config(config)
            return

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_provider_config (
                    singleton_id,
                    base_url,
                    model,
                    api_key,
                    timeout_seconds,
                    updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    base_url = excluded.base_url,
                    model = excluded.model,
                    api_key = excluded.api_key,
                    timeout_seconds = excluded.timeout_seconds,
                    updated_at = excluded.updated_at
                """,
                (
                    config.base_url.strip(),
                    config.model.strip(),
                    config.api_key,
                    config.timeout_seconds,
                    datetime.now().astimezone().isoformat(),
                ),
            )

    def clear(self) -> None:
        if self._profile != "default":
            with self._connect() as connection:
                connection.execute(
                    """
                    DELETE FROM ai_agent_provider_configs
                    WHERE agent_id = ?
                    """,
                    (self._profile,),
                )
            return

        with self._connect() as connection:
            connection.execute(
                "DELETE FROM ai_provider_config WHERE singleton_id = 1"
            )

    def _load_agent_config(self) -> ProviderConfig | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT base_url, model, api_key, timeout_seconds
                FROM ai_agent_provider_configs
                WHERE agent_id = ?
                """,
                (self._profile,),
            ).fetchone()
        if row is None:
            return None
        return ProviderConfig(
            base_url=row["base_url"],
            model=row["model"],
            api_key=row["api_key"],
            timeout_seconds=float(row["timeout_seconds"]),
        )

    def _save_agent_config(self, config: ProviderConfig) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_agent_provider_configs (
                    agent_id,
                    base_url,
                    model,
                    api_key,
                    timeout_seconds,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    base_url = excluded.base_url,
                    model = excluded.model,
                    api_key = excluded.api_key,
                    timeout_seconds = excluded.timeout_seconds,
                    updated_at = excluded.updated_at
                """,
                (
                    self._profile,
                    config.base_url.strip(),
                    config.model.strip(),
                    config.api_key,
                    config.timeout_seconds,
                    datetime.now().astimezone().isoformat(),
                ),
            )


class SQLiteSummaryResultStore(_SQLiteStore):
    """Stores generated summaries locally and loads the latest per article."""

    def save(self, result: SummaryResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_summary_results (
                    article_id,
                    summary_text,
                    language,
                    detail_level,
                    source_format,
                    generated_at,
                    provider_model,
                    status,
                    error_code,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.article_id,
                    result.text,
                    result.language,
                    result.detail_level.value,
                    result.source_format.value,
                    result.generated_at.isoformat(),
                    result.provider_model,
                    result.status.value,
                    result.error_code.value if result.error_code else None,
                    result.error_message,
                ),
            )
            _delete_old_results(
                connection,
                table="ai_summary_results",
                article_id=result.article_id,
            )

    def latest_for_article(self, article_id: str) -> SummaryResult | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    article_id,
                    summary_text,
                    language,
                    detail_level,
                    source_format,
                    generated_at,
                    provider_model,
                    status,
                    error_code,
                    error_message
                FROM ai_summary_results
                WHERE article_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (article_id,),
            ).fetchone()

        if row is None:
            return None

        return SummaryResult(
            article_id=row["article_id"],
            text=row["summary_text"],
            language=row["language"],
            detail_level=SummaryDetail(row["detail_level"]),
            source_format=SummarySourceFormat(row["source_format"]),
            generated_at=datetime.fromisoformat(row["generated_at"]),
            provider_model=row["provider_model"],
            status=SummaryStatus(row["status"]),
            error_code=(
                SummaryErrorCode(row["error_code"])
                if row["error_code"]
                else None
            ),
            error_message=row["error_message"],
        )


class SQLiteTranslationResultStore(_SQLiteStore):
    """Stores paragraph-aligned translations in one atomic transaction."""

    def save(self, result: TranslationResult) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ai_translation_results (
                    article_id,
                    target_language,
                    source_format,
                    generated_at,
                    provider_model,
                    status,
                    is_saved,
                    error_code,
                    error_message,
                    storage_error_code,
                    storage_error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.article_id,
                    result.target_language,
                    result.source_format.value,
                    result.generated_at.isoformat(),
                    result.provider_model,
                    result.status.value,
                    int(result.is_saved),
                    result.error_code.value if result.error_code else None,
                    result.error_message,
                    (
                        result.storage_error_code.value
                        if result.storage_error_code
                        else None
                    ),
                    result.storage_error_message,
                ),
            )
            result_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO ai_translation_paragraphs (
                    result_id,
                    paragraph_index,
                    original_text,
                    translated_text,
                    status,
                    segment_count,
                    translated_segment_count,
                    error_code,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        result_id,
                        paragraph.index,
                        paragraph.original_text,
                        paragraph.translated_text,
                        paragraph.status.value,
                        paragraph.segment_count,
                        paragraph.translated_segment_count,
                        (
                            paragraph.error_code.value
                            if paragraph.error_code
                            else None
                        ),
                        paragraph.error_message,
                    )
                    for paragraph in result.paragraphs
                ),
            )
            _delete_old_results(
                connection,
                table="ai_translation_results",
                article_id=result.article_id,
            )

    def latest_for_article(
        self,
        article_id: str,
    ) -> TranslationResult | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    article_id,
                    target_language,
                    source_format,
                    generated_at,
                    provider_model,
                    status,
                    is_saved,
                    error_code,
                    error_message,
                    storage_error_code,
                    storage_error_message
                FROM ai_translation_results
                WHERE article_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (article_id,),
            ).fetchone()
            if row is None:
                return None

            paragraph_rows = connection.execute(
                """
                SELECT
                    paragraph_index,
                    original_text,
                    translated_text,
                    status,
                    segment_count,
                    translated_segment_count,
                    error_code,
                    error_message
                FROM ai_translation_paragraphs
                WHERE result_id = ?
                ORDER BY paragraph_index
                """,
                (row["id"],),
            ).fetchall()

        paragraphs = tuple(
            TranslationParagraph(
                index=paragraph["paragraph_index"],
                original_text=paragraph["original_text"],
                translated_text=paragraph["translated_text"],
                status=TranslationParagraphStatus(paragraph["status"]),
                segment_count=paragraph["segment_count"],
                translated_segment_count=(
                    paragraph["translated_segment_count"]
                ),
                error_code=(
                    TranslationErrorCode(paragraph["error_code"])
                    if paragraph["error_code"]
                    else None
                ),
                error_message=paragraph["error_message"],
            )
            for paragraph in paragraph_rows
        )
        return TranslationResult(
            article_id=row["article_id"],
            target_language=row["target_language"],
            paragraphs=paragraphs,
            source_format=TranslationSourceFormat(row["source_format"]),
            generated_at=datetime.fromisoformat(row["generated_at"]),
            provider_model=row["provider_model"],
            status=TranslationStatus(row["status"]),
            is_saved=bool(row["is_saved"]),
            error_code=(
                TranslationErrorCode(row["error_code"])
                if row["error_code"]
                else None
            ),
            error_message=row["error_message"],
            storage_error_code=(
                TranslationErrorCode(row["storage_error_code"])
                if row["storage_error_code"]
                else None
            ),
            storage_error_message=row["storage_error_message"],
        )


def _delete_old_results(
    connection: sqlite3.Connection,
    *,
    table: str,
    article_id: str,
) -> None:
    if table not in {
        "ai_summary_results",
        "ai_translation_results",
    }:
        raise ValueError("Unsupported AI result table.")

    connection.execute(
        f"""
        DELETE FROM {table}
        WHERE article_id = ?
          AND id NOT IN (
              SELECT id
              FROM {table}
              WHERE article_id = ?
              ORDER BY id DESC
              LIMIT ?
          )
        """,
        (article_id, article_id, _MAX_RESULTS_PER_ARTICLE),
    )
