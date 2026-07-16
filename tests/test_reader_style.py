import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.ui.reader_style import InMemoryReaderStyleStore, ReaderStyle


class ReaderStyleTest(unittest.TestCase):
    def test_defaults_are_suitable_for_reader_view(self) -> None:
        style = ReaderStyle()

        self.assertEqual(style.font_size, 18)
        self.assertEqual(style.line_height, 1.6)
        self.assertEqual(style.content_width, 820)

    def test_normalization_keeps_values_in_supported_ranges(self) -> None:
        style = ReaderStyle(
            font_size=100,
            line_height=0.5,
            content_width=100,
        ).normalized()

        self.assertEqual(style.font_size, 32)
        self.assertEqual(style.line_height, 1.2)
        self.assertEqual(style.content_width, 480)

    def test_in_memory_store_can_be_replaced_by_persistent_adapter(self) -> None:
        store = InMemoryReaderStyleStore()
        updated = ReaderStyle(font_size=24, line_height=2.0, content_width=680)

        store.save(updated)

        self.assertEqual(store.load(), updated)
