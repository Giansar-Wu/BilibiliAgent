import sys
import get_path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap, QIcon, QColor, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout

class AppWindow(QMainWindow):
    def __init__() -> None:
        super().__init__()

class ScanWindow(QWidget):
    def __init__(self, qr_width: int=250) -> None:
        super().__init__()

        self.setWindowTitle("扫码登录")
        self.setWindowIcon(QIcon(F"{get_path.RESOURCE_PATH}/icons/bilibili.png"))

        self.text_label = QLabel("请使用 bilibili 客户端扫码登陆")
        font = self.text_label.font()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(22)
        self.text_label.setFont(font)
        palette = self.text_label.palette()
        palette.setColor(QPalette.WindowText, QColor(251, 114, 153))
        self.text_label.setPalette(palette)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setFixedWidth(qr_width)
        # self.text_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.qrcode_label = QLabel()
        self.qrcode_label.setPixmap(QPixmap(F"{get_path.RESOURCE_PATH}/data/test.jpeg").scaled(QSize(qr_width,qr_width)))
        self.qrcode_label.setAlignment(Qt.AlignCenter)
        self.qrcode_label.setFixedSize(QSize(qr_width,qr_width))
        # self.qrcode_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        print(self.qrcode_label.sizeHint())

        self.refresh_button = QPushButton(QIcon(F"{get_path.RESOURCE_PATH}/icons/refresh.png"), "点击\n刷新", self.qrcode_label)
        font = self.refresh_button.font()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(20)
        self.refresh_button.setFont(font)
        palette = self.refresh_button.palette()
        palette.setColor(QPalette.WindowText, QColor(135, 206, 250))
        self.refresh_button.setPalette(palette)
        self.refresh_button.setIconSize(QSize(40,40))
        self.refresh_button.setFixedWidth(100)
        layout = QHBoxLayout()
        layout.addWidget(self.refresh_button)
        self.qrcode_label.setLayout(layout)
        self.refresh_button.setChecked(True)
        self.refresh_button.clicked.connect(self.refresh)
        # self.refresh_button.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.qrcode_label)
        self.setLayout(layout)

        self.setFixedSize(self.sizeHint())

    def refresh(self):
        self.qrcode_label.setPixmap(QPixmap(F"{get_path.RESOURCE_PATH}/data/qrcode.png").scaled(self.qrcode_label.sizeHint()))
        self.refresh_button.hide()

    def overdue(self):
        self.qrcode_label.setPixmap(QPixmap(F"{get_path.RESOURCE_PATH}/data/qrcode.png").scaled(self.qrcode_label.sizeHint()))
        self.refresh_button.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ScanWindow()
    window.show()

    app.exec()