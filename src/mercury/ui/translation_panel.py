from collections.abc import Callable
import inspect

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from mercury.agents import TranslationOptions, TranslationSource
from mercury.domain import (
    TranslationErrorCode,
    TranslationResult,
    TranslationStatus,
)
from mercury.i18n import Translator


TranslationGenerator = Callable[..., TranslationResult]
TranslationResultLoader = Callable[[str], TranslationResult | None]


class _TranslationWorkerSignals(QObject):
    progress = Signal(int, object)
    completed = Signal(int, object)
    failed = Signal(int)


class _TranslationWorker(QRunnable):
    def __init__(
        self,
        token: int,
        generator: TranslationGenerator,
        source: TranslationSource,
        options: TranslationOptions,
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.token = token
        self.generator = generator
        self.source = source
        self.options = options
        self.signals = _TranslationWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            if self._supports_progress_callback():
                result = self.generator(
                    self.source,
                    self.options,
                    progress_callback=self._emit_progress,
                )
            else:
                result = self.generator(self.source, self.options)
        except Exception:
            self.signals.failed.emit(self.token)
            return

        self.signals.completed.emit(self.token, result)

    def _supports_progress_callback(self) -> bool:
        try:
            parameters = inspect.signature(self.generator).parameters
        except (TypeError, ValueError):
            return False

        return (
            "progress_callback" in parameters
            or any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )
        )

    def _emit_progress(self, result: TranslationResult) -> None:
        self.signals.progress.emit(self.token, result)


class TranslationPanel(QFrame):
    """Compact controls for generating Reader-embedded translations."""

    settings_requested = Signal()
    generation_progress = Signal(object)
    generation_completed = Signal(object)
    generation_failed = Signal()

    _LANGUAGES = (
        ("translation.language.zh_cn", "Simplified Chinese"),
        ("translation.language.en_us", "English"),
    )
    _ERROR_KEYS = {
        TranslationErrorCode.INVALID_INPUT: "translation.error.invalid_input",
        TranslationErrorCode.PROVIDER_NOT_CONFIGURED: (
            "translation.error.provider_not_configured"
        ),
        TranslationErrorCode.PROVIDER_FAILURE: (
            "translation.error.provider_failure"
        ),
        TranslationErrorCode.EMPTY_RESPONSE: (
            "translation.error.empty_response"
        ),
        TranslationErrorCode.WRONG_LANGUAGE: (
            "translation.error.wrong_language"
        ),
        TranslationErrorCode.INCOMPLETE_RESPONSE: (
            "translation.error.incomplete_response"
        ),
        TranslationErrorCode.STORAGE_FAILURE: (
            "translation.status.storage_warning"
        ),
    }

    def __init__(
        self,
        translator: Translator,
        generator: TranslationGenerator | None = None,
        result_loader: TranslationResultLoader | None = None,
        thread_pool: QThreadPool | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("TranslationPanel")
        self._translator = translator
        self._generator = generator
        self._result_loader = result_loader
        self._thread_pool = thread_pool or QThreadPool(self)
        self._current_source: TranslationSource | None = None
        self._displayed_result: TranslationResult | None = None
        self._result_cache: dict[str, TranslationResult] = {}
        self._workers: dict[int, _TranslationWorker] = {}
        self._generation_token = 0
        self._active_token = 0
        self._is_running = False
        self._state = "no_article"
        self._last_error_code: TranslationErrorCode | None = None

        self.language_label = QLabel()
        self.language_label.setObjectName("TranslationFieldLabel")
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("TranslationControl")

        self.prompt_label = QLabel()
        self.prompt_label.setObjectName("TranslationFieldLabel")
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setObjectName("TranslationPrompt")
        self.prompt_edit.setFixedHeight(58)

        self.generate_button = QPushButton()
        self.generate_button.setObjectName("TranslationActionButton")
        self.generate_button.clicked.connect(self.generate_translation)

        self.configure_button = QPushButton()
        self.configure_button.setObjectName("TranslationSecondaryButton")
        self.configure_button.clicked.connect(self.settings_requested.emit)

        self.status_label = QLabel()
        self.status_label.setObjectName("TranslationStatus")
        self.status_label.setWordWrap(True)

        self.timestamp_label = QLabel()
        self.timestamp_label.setObjectName("TranslationTimestamp")

        self.result_location_label = QLabel()
        self.result_location_label.setObjectName(
            "TranslationResultLocation"
        )
        self.result_location_label.setWordWrap(True)

        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setHorizontalSpacing(8)
        controls_layout.setVerticalSpacing(6)
        controls_layout.addWidget(self.language_label, 0, 0)
        controls_layout.addWidget(self.language_combo, 0, 1)
        controls_layout.addWidget(self.prompt_label, 1, 0)
        controls_layout.addWidget(self.prompt_edit, 1, 1)
        controls_layout.setColumnStretch(1, 1)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addWidget(self.generate_button)
        action_layout.addWidget(self.configure_button)
        action_layout.addWidget(self.status_label, 1)
        action_layout.addWidget(self.timestamp_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addLayout(controls_layout)
        layout.addLayout(action_layout)
        layout.addWidget(self.result_location_label)

        self.set_translator(translator)
        self.clear_article()

    @property
    def current_article_id(self) -> str | None:
        if self._current_source is None:
            return None

        return self._current_source.article_id

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def displayed_result(self) -> TranslationResult | None:
        return self._displayed_result

    def set_article(self, source: TranslationSource) -> None:
        self._invalidate_active_generation()
        self._current_source = source
        self._last_error_code = None

        result = self._result_cache.get(source.article_id)
        if result is None and self._result_loader is not None:
            try:
                result = self._result_loader(source.article_id)
            except Exception:
                self._displayed_result = None
                self._state = "load_failed"
                self._render_state()
                return

        if result is not None and result.paragraphs:
            self._result_cache[source.article_id] = result
            self._show_result(result)
            return

        self._displayed_result = None
        self._state = "ready" if self._generator is not None else "unavailable"
        self._render_state()

    def clear_article(self) -> None:
        self._invalidate_active_generation()
        self._current_source = None
        self._displayed_result = None
        self._last_error_code = None
        self._state = "no_article"
        self._render_state()

    def set_translator(self, translator: Translator) -> None:
        self._translator = translator
        self.language_label.setText(
            translator.text("translation.target_language")
        )
        self.prompt_label.setText(
            translator.text("translation.custom_prompt")
        )
        self.prompt_edit.setPlaceholderText(
            translator.text("translation.custom_prompt_placeholder")
        )
        self.configure_button.setText(
            translator.text("translation.configure_ai")
        )
        self.result_location_label.setText(
            translator.text("translation.result_location")
        )
        self._replace_combo_items(
            [
                (translator.text(label_key), value)
                for label_key, value in self._LANGUAGES
            ],
            default_value="Simplified Chinese",
        )
        self._render_state()

    def set_color_scheme(self, theme: str) -> None:
        is_light = theme == "light"
        text_color = QColor("#1f2933" if is_light else "#f3f6f9")
        placeholder_color = QColor(
            "#66717c" if is_light else "#b6c3cf"
        )
        base_color = QColor("#ffffff" if is_light else "#202833")

        palette = self.prompt_edit.palette()
        palette.setColor(QPalette.ColorRole.Text, text_color)
        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            placeholder_color,
        )
        palette.setColor(QPalette.ColorRole.Base, base_color)
        self.prompt_edit.setPalette(palette)

        combo_palette = self.language_combo.palette()
        combo_palette.setColor(QPalette.ColorRole.Text, text_color)
        combo_palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        combo_palette.setColor(QPalette.ColorRole.Base, base_color)
        self.language_combo.setPalette(combo_palette)

    @Slot()
    def generate_translation(self) -> None:
        if self._current_source is None or self._is_running:
            return

        if self._generator is None:
            self._state = "unavailable"
            self._render_state()
            self.settings_requested.emit()
            return

        options = TranslationOptions(
            target_language=str(self.language_combo.currentData()),
            custom_prompt=self.prompt_edit.toPlainText(),
        )
        self._generation_token += 1
        token = self._generation_token
        self._active_token = token
        self._is_running = True
        self._state = "running"
        self._render_state()

        worker = _TranslationWorker(
            token,
            self._generator,
            self._current_source,
            options,
        )
        worker.signals.progress.connect(self._handle_progress)
        worker.signals.completed.connect(self._handle_completed)
        worker.signals.failed.connect(self._handle_failed)
        self._workers[token] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _handle_progress(self, token: int, value: object) -> None:
        if (
            token != self._active_token
            or self._current_source is None
            or not isinstance(value, TranslationResult)
            or value.article_id != self._current_source.article_id
            or not value.paragraphs
        ):
            return

        self._displayed_result = value
        self._result_cache[value.article_id] = value
        self._state = "running"
        self._render_state()
        self.generation_progress.emit(value)

    @Slot(int, object)
    def _handle_completed(self, token: int, value: object) -> None:
        self._workers.pop(token, None)

        if token != self._active_token or self._current_source is None:
            return

        self._is_running = False
        if not isinstance(value, TranslationResult):
            self._state = "unexpected_failure"
            self._render_state()
            self.generation_failed.emit()
            return

        result = value
        if result.article_id != self._current_source.article_id:
            self._state = "unexpected_failure"
            self._render_state()
            self.generation_failed.emit()
            return

        if result.paragraphs:
            self._result_cache[result.article_id] = result
            self._show_result(result)
        else:
            self._last_error_code = result.error_code
            self._state = "result_failure"
            self._render_state()

        self.generation_completed.emit(result)

    @Slot(int)
    def _handle_failed(self, token: int) -> None:
        self._workers.pop(token, None)

        if token != self._active_token or self._current_source is None:
            return

        self._is_running = False
        self._last_error_code = None
        self._state = "unexpected_failure"
        self._render_state()
        self.generation_failed.emit()

    def _show_result(self, result: TranslationResult) -> None:
        self._displayed_result = result
        self._last_error_code = result.error_code

        if result.storage_error_code is not None:
            self._state = "storage_warning"
        elif result.status is TranslationStatus.COMPLETED:
            self._state = "completed"
        elif result.status is TranslationStatus.PARTIAL:
            self._state = "partial"
        else:
            self._state = "result_failure"

        self._render_state()

    def _render_state(self) -> None:
        state_keys = {
            "no_article": "translation.status.no_article",
            "unavailable": "translation.status.unavailable",
            "ready": "translation.status.ready",
            "running": "translation.status.running",
            "completed": "translation.status.completed",
            "partial": "translation.status.partial",
            "storage_warning": "translation.status.storage_warning",
            "load_failed": "translation.error.load_failed",
            "unexpected_failure": "translation.error.unexpected",
        }

        if self._state == "result_failure":
            key = self._ERROR_KEYS.get(
                self._last_error_code,
                "translation.status.failed",
            )
        else:
            key = state_keys.get(
                self._state,
                "translation.error.unexpected",
            )

        self.status_label.setText(self._translator.text(key))
        self.generate_button.setText(
            self._translator.text(
                "translation.regenerate"
                if self._displayed_result is not None
                else "translation.generate"
            )
        )
        self.generate_button.setEnabled(
            self._current_source is not None
            and not self._is_running
        )
        if self._current_source is None:
            tooltip_key = "translation.generate_tooltip.no_article"
        elif self._generator is None:
            tooltip_key = "translation.generate_tooltip.configure"
        else:
            tooltip_key = "translation.generate_tooltip.ready"
        self.generate_button.setToolTip(
            self._translator.text(tooltip_key)
        )

        if self._displayed_result is None:
            self.timestamp_label.clear()
            return

        generated_at = self._displayed_result.generated_at.astimezone()
        self.timestamp_label.setText(
            self._translator.text("translation.generated_at").format(
                time=generated_at.strftime("%Y-%m-%d %H:%M"),
            )
        )

    def _replace_combo_items(
        self,
        items: list[tuple[str, str]],
        default_value: str,
    ) -> None:
        current_data = self.language_combo.currentData()
        selected_data = (
            str(current_data)
            if current_data is not None
            else default_value
        )
        self.language_combo.clear()

        for label, value in items:
            self.language_combo.addItem(label, value)

        index = self.language_combo.findData(selected_data)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

    def _invalidate_active_generation(self) -> None:
        self._generation_token += 1
        self._active_token = self._generation_token
        self._is_running = False
