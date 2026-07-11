from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt

def _create_icon():
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#7C3AED"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 18, 18)
    p.end()
    return QIcon(pixmap)

class TrayManager:
    def __init__(self, overlay):
        self.overlay = overlay
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_create_icon())
        menu = QMenu()
        test_action = menu.addAction("Show Overlay (test)")
        test_action.triggered.connect(self._test_show)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        self.tray.setContextMenu(menu)

    def show(self):
        self.tray.show()

    def _test_show(self):
        from PySide6.QtGui import QCursor
        pos = QCursor.pos()
        self.overlay.show_at(pos.x(), pos.y(), "Testing overlay position...")