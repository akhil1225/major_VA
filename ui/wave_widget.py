import math

from PySide6.QtWidgets import QWidget #type:ignore
from PySide6.QtCore import QTimer, Qt, Slot # type: ignore
from PySide6.QtGui import QPainter, QColor # type: ignore


class WaveWidget(QWidget):
    """
    Siri-style speaking animation.
    State-driven (not audio-driven).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._phase = 0.0
        self._amplitude = 8
        self._active = False

        self.setFixedHeight(70)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)

    @Slot()
    def start(self):
        self._active = True
        self._timer.start()
        self.update()

    @Slot()
    def stop(self):
        self._active = False
        self._timer.stop()
        self.update()

    def _tick(self):
        self._phase += 0.25
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._active:
            return

        w = self.width()
        h = self.height()
        center = h // 2

        colors = [
            QColor(255, 80, 80),
            QColor(80, 160, 255),
            QColor(100, 220, 180),
            QColor(255, 200, 100),
        ]

        for i, color in enumerate(colors):
            painter.setPen(color)
            offset = (i - 1.5) * 6

            prev_x = 0
            prev_y = center

            for x in range(0, w, 4):
                y = center + offset + math.sin(
                    (x / 50.0) + self._phase + i
                ) * self._amplitude

                painter.drawLine(prev_x, prev_y, x, y)
                prev_x, prev_y = x, y
