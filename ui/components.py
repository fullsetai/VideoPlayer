from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt

class ClickableSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos().x()
            value = self.minimum() + (self.maximum() - self.minimum()) * pos / self.width()
            self.setValue(int(value))
            self.sliderReleased.emit()
        super().mousePressEvent(event)