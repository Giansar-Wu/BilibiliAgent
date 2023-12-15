import os
import sys
from multiprocessing import Process

from PySide6.QtGui import (QIcon, QGuiApplication)
from PySide6.QtWidgets import (QMainWindow, QApplication, QWidget, QGridLayout, QLineEdit, QComboBox, QLabel, QCheckBox,  QFileDialog, QPushButton, QTextBrowser)

import bilibili_agent2

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QGuiApplication.primaryScreen().geometry()
        self.setWindowTitle('Bilibili Downloader')
        self.setFixedSize(int(screen.width()/4), int(screen.height()/4))
        icon = QIcon()
        icon.addFile(os.path.join(bilibili_agent2.ROOT_PATH, "resources", "icons", "bilibili.png"))
        self.setWindowIcon(icon)
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self._init_ui()
        self._connect()
        self.agent = bilibili_agent2.BilibiliAgent()

    def _init_ui(self):
        self.central_layout = QGridLayout(self.central_widget)
        self.central_widget.setLayout(self.central_layout)

        # bv input 
        self.bv_input = QLineEdit(self.central_widget)
        self.bv_input.setObjectName("bv_input")
        self.bv_input.setPlaceholderText("请输入bv号或者视频网页链接")
        self.central_layout.addWidget(self.bv_input, 0, 0, 2, 5)

        # get videos info button
        self.get_info_button = QPushButton(self.central_widget)
        self.get_info_button.setText("资源解析")
        self.central_layout.addWidget(self.get_info_button, 0, 5, 2, 1)

        # video qultiy label
        self.video_qulity_label = QLabel(self.central_widget)
        self.video_qulity_label.setText("视频清晰度")
        self.central_layout.addWidget(self.video_qulity_label, 2, 0, 1, 1)

        # video qulity select
        self.video_quality_select = QComboBox(self.central_widget)
        self.central_layout.addWidget(self.video_quality_select, 2, 1, 1, 2)

        # video codec label
        self.video_code_label = QLabel(self.central_widget)
        self.video_code_label.setText("视频编码")
        self.central_layout.addWidget(self.video_code_label, 2, 3, 1, 1)

        # video codec select
        self.video_codec_select = QComboBox(self.central_widget)
        self.central_layout.addWidget(self.video_codec_select, 2, 4, 1, 2)

        # audio qulity label
        self.video_qulity_label = QLabel(self.central_widget)
        self.video_qulity_label.setText("音频清晰度")
        self.central_layout.addWidget(self.video_qulity_label, 3, 0, 1, 1)

        # audio qulity select
        self.audio_quality_select = QComboBox(self.central_widget)
        self.central_layout.addWidget(self.audio_quality_select, 3, 1, 1, 2)

        # audio save label
        self.audio_save_label = QLabel(self.central_widget)
        self.audio_save_label.setText("保存音频")
        self.central_layout.addWidget(self.audio_save_label, 3, 3, 1, 1)

        # audio save box
        self.audio_save_box = QCheckBox(self.central_widget)
        self.central_layout.addWidget(self.audio_save_box, 3, 4, 1, 2)

        # save path display
        self.save_path_display = QLineEdit(self.central_widget)
        self.save_path_display.setReadOnly(True)
        self.save_path_display.setText(os.path.join(bilibili_agent2.USER_PATH, 'Desktop'))
        self.central_layout.addWidget(self.save_path_display, 4, 0, 1, 5)

        # save path button 
        self.save_path_button = QPushButton(self.central_widget)
        self.save_path_button.setText("选择保存目录")
        self.central_layout.addWidget(self.save_path_button, 4, 5, 1, 1)

        # title label
        self.title_label = QLabel(self.central_widget)
        self.title_label.setText("视频标题")
        self.central_layout.addWidget(self.title_label, 5, 0, 1, 1)

        # title display
        self.title_display = QLineEdit(self.central_widget)
        self.title_display.setReadOnly(True)
        self.central_layout.addWidget(self.title_display, 5, 1, 1, 4)

        # download button 
        self.download_button = QPushButton(self.central_widget)
        self.download_button.setText("开始下载")
        self.central_layout.addWidget(self.download_button, 5, 5, 1, 1)

        # log display
        self.log_display = QTextBrowser(self.central_widget)
        self.central_layout.addWidget(self.log_display, 6, 0, 3, 6)

    def _connect(self):
        self.get_info_button.clicked.connect(self._bv_resolve_event)
        self.video_quality_select.currentTextChanged.connect(self._video_quality_change)
        self.save_path_button.clicked.connect(self._select_save_path_event)
        self.download_button.clicked.connect(self._download_event)

    def _set_widgets(self, resolve_ret: dict):
        self.resolve_ret = resolve_ret
        # set title
        self.title_display.setText(resolve_ret['title'])
        # set video
        self.video_quality_select.clear() 
        self.video_quality_select.addItems(list(resolve_ret['videos'].keys()))
        self.video_quality_select.setCurrentIndex(0)
        # set audio
        self.audio_quality_select.clear()
        self.audio_quality_select.addItems(list(resolve_ret['audios'].keys()))
        self.audio_quality_select.setCurrentIndex(0)
    
    def _video_quality_change(self):
        current_quality = self.video_quality_select.currentText()
        self.video_codec_select.clear()
        self.video_codec_select.addItems(list(self.resolve_ret['videos'][current_quality].keys()))
    
    def _bv_resolve_event(self):
        bv_or_url = self.bv_input.text()
        check, ret = self.agent.get_info(bv_or_url, True)
        if check:
            self._set_widgets(ret)
    
    def _select_save_path_event(self):
        filepath = QFileDialog.getExistingDirectory(self.central_widget,dir=bilibili_agent2.USER_PATH)
        self.save_path_display.setText(filepath)

    def _download_event(self):
        # get video info
        video_quality = self.video_quality_select.currentText()
        video_codec = self.video_codec_select.currentText()
        video = self.resolve_ret['videos'][video_quality][video_codec][0]
        # get audio
        audio_quality = self.audio_quality_select.currentText()
        audio = self.resolve_ret['audios'][audio_quality][0]
        # get path
        save_path = self.save_path_display.text()
        # get save audio
        save_audio = self.audio_save_box.isChecked()
        p = Process(target=self.agent.download,args=(video, audio, save_audio, save_path))
        p.daemon = True 
        p.start()
        # self.agent.download(video, audio, save_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyMainWindow()
    win.show()
    app.exec()