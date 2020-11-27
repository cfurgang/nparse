from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)

from helpers import config


class ParserWindow(QFrame):

    def __init__(self):
        super().__init__()
        self.name = ''
        self.setObjectName('ParserWindow')
        self.setWindowOpacity(config.data['general']['parser_opacity'] / 100)
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self.setLayout(self.content)
        self._menu = QWidget()
        self._menu_content = QHBoxLayout()
        self._menu.setLayout(self._menu_content)
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 0, 0, 0)
        self.content.addWidget(self._menu, 0)

        self._title = QLabel()
        self._title.setObjectName('ParserWindowTitle')

        button = QPushButton(u'\u2637')
        button.setObjectName('ParserWindowMoveButton')
        self._menu_content.addWidget(button, 0)
        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        menu_area.setObjectName('ParserWindowMenu')
        self.menu_area = QHBoxLayout()
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)
        self._menu.setVisible(False)

        button.clicked.connect(self._toggle_frame)

    def set_flags(self):
        self.setFocus()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinMaxButtonsHint
        )
        self.show()

    def _toggle_frame(self):
        current_geometry = self.geometry()
        if bool(self.windowFlags() & Qt.FramelessWindowHint):
            self.setWindowFlags(
                Qt.WindowCloseButtonHint |
                Qt.WindowMinMaxButtonsHint
            )
            self.setGeometry(current_geometry)
            self.show()
        else:
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint
            )
            self.setGeometry(current_geometry)
            self.show()
        g = self.geometry()

    def set_title(self, title):
        self._title.setText(title)

    def toggle(self, _=None):
        if self.isVisible():
            self.hide()
            config.data[self.name]['toggled'] = False
        else:
            self.set_flags()
            self.show()
            config.data[self.name]['toggled'] = True
        config.save()

    def closeEvent(self, _):
        config.data[self.name]['toggled'] = False
        config.save()

    def enterEvent(self, event):
        self._menu.setVisible(True)
        QFrame.enterEvent(self, event)

    def leaveEvent(self, event):
        self._menu.setVisible(False)
        QFrame.leaveEvent(self, event)

    def settings_updated(self):
        pass
