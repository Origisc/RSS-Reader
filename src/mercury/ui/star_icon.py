from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen


def draw_star(
    painter: QPainter,
    bounds: QRectF,
    *,
    filled: bool,
    color: QColor,
) -> None:
    """Draw a font-independent five-point star inside ``bounds``."""
    path = _star_path(bounds)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(color, 1.5))
    painter.setBrush(
        color if filled else Qt.BrushStyle.NoBrush
    )
    painter.drawPath(path)
    painter.restore()


def _star_path(bounds: QRectF) -> QPainterPath:
    center = bounds.center()
    outer_radius = min(bounds.width(), bounds.height()) / 2
    inner_radius = outer_radius * 0.44
    path = QPainterPath()

    for index in range(10):
        radius = outer_radius if index % 2 == 0 else inner_radius
        angle = -math.pi / 2 + index * math.pi / 5
        point = QPointF(
            center.x() + math.cos(angle) * radius,
            center.y() + math.sin(angle) * radius,
        )
        if index == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)

    path.closeSubpath()
    return path
