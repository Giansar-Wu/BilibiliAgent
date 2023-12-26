import os
import sys
import time
import datetime
from threading import Thread

from PySide6.QtCore import Qt, QSize, QObject, Signal, QThread
from PySide6.QtGui import QCloseEvent, QIcon, QGuiApplication, QPixmap, QColor, QImage, QPainter, QTextCursor
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QLineEdit, QComboBox, QLabel, QCheckBox,  QFileDialog, QPushButton, QTextEdit

import bilibili_agent2

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QGuiApplication.primaryScreen().geometry()
        self.setWindowTitle('Bilibili Video Downloader')
        self.setFixedSize(int(screen.width()/2.5), int(screen.height()/3))
        icon = QIcon()
        icon.addFile(os.path.join(bilibili_agent2.ROOT_PATH, "resources", "icons", "bilibili.png"))
        self.setWindowIcon(icon)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self._init_ui()
        self._connect()
        self.agent = bilibili_agent2.BilibiliAgent()
        self._update_login()

        self.stream = Stream()
        self.stream.stream_update.connect(self._write_log_info)
        sys.stdout = self.stream
        sys.stderr = self.stream

        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bilibili Downloader start!")

    def _init_ui(self):
        cols = 10
        self.central_layout = QGridLayout(self.central_widget)
        self.central_widget.setLayout(self.central_layout)

        for i in range(cols):
            self.central_layout.setColumnMinimumWidth(i, 1)
            self.central_layout.setColumnStretch(i, 1)

        # login button
        self.login_button = QPushButton(self.central_widget)
        self.central_layout.addWidget(self.login_button, 0, 0, 1, 1)

        # login disply
        self.login_display = QLineEdit(self.central_widget)
        self.login_display.setReadOnly(True)
        self.central_layout.addWidget(self.login_display, 0, 1, 1, 4)   

        # add space
        self.space_label = QLabel(self.central_widget)
        self.central_layout.addWidget(self.space_label, 0, 5, 1, 5)

        # bv input 
        self.bv_input = QLineEdit(self.central_widget)
        self.bv_input.setPlaceholderText("请输入bv号或者视频网页链接")
        self.central_layout.addWidget(self.bv_input, 1, 0, 1, 9)

        # get videos info button
        self.get_info_button = QPushButton(self.central_widget)
        self.get_info_button.setText("资源解析")
        self.central_layout.addWidget(self.get_info_button, 1, 9, 1, 1)

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
        self.central_layout.addWidget(self.video_codec_select, 2, 4, 1, 1)

        # audio qulity label
        self.video_qulity_label = QLabel(self.central_widget)
        self.video_qulity_label.setText("音频清晰度")
        self.central_layout.addWidget(self.video_qulity_label, 2, 5, 1, 1)

        # audio qulity select
        self.audio_quality_select = QComboBox(self.central_widget)
        self.central_layout.addWidget(self.audio_quality_select, 2, 6, 1, 2)

        # audio save label
        self.audio_save_label = QLabel(self.central_widget)
        self.audio_save_label.setText("保存音频")
        self.central_layout.addWidget(self.audio_save_label, 2, 8, 1, 1)

        # audio save box
        self.audio_save_box = QCheckBox(self.central_widget)
        self.central_layout.addWidget(self.audio_save_box, 2, 9, 1, 1)

        # save path display
        self.save_path_display = QLineEdit(self.central_widget)
        self.save_path_display.setReadOnly(True)
        self.save_path_display.setText(os.path.join(bilibili_agent2.USER_PATH, 'Desktop'))
        self.central_layout.addWidget(self.save_path_display, 3, 0, 1, 8)

        # save path button 
        self.save_path_button = QPushButton(self.central_widget)
        self.save_path_button.setText("选择保存目录")
        self.central_layout.addWidget(self.save_path_button, 3, 8, 1, 2)

        # title label
        self.title_label = QLabel(self.central_widget)
        self.title_label.setText("视频标题")
        self.central_layout.addWidget(self.title_label, 4, 0, 1, 1)

        # title display
        self.title_display = QLineEdit(self.central_widget)
        self.title_display.setReadOnly(True)
        self.central_layout.addWidget(self.title_display, 4, 1, 1, 8)

        # download button 
        self.download_button = QPushButton(self.central_widget)
        self.download_button.setText("开始下载")
        self.central_layout.addWidget(self.download_button, 4, 9, 1, 1)

        # log display
        self.log_display = QTextEdit(self.central_widget)
        self.log_display.setReadOnly(True)
        self.central_layout.addWidget(self.log_display, 5, 0, 4, 10)

    def _connect(self):
        self.get_info_button.clicked.connect(self._bv_resolve_event)
        self.video_quality_select.currentTextChanged.connect(self._video_quality_change)
        self.save_path_button.clicked.connect(self._select_save_path_event)
        self.download_button.clicked.connect(self._download_event)
        self.login_button.clicked.connect(self._login_event)

    def _update_login(self):
        login = self.agent.get_login_state()
        if login:
            self.login_button.setText("注销")
            self.login_display.setText(F"{self.agent.user_info['uname']}  Lv{self.agent.user_info['level']}  {self.agent.user_info['vip']}")
        else:
            self.login_button.setText("扫码登录")
            self.login_display.setText("账号未登录！")

    def _set_widgets(self, resolve_ret: dict):
        self.resolve_ret = resolve_ret
        # set title
        self.title_display.setText(resolve_ret['title'])
        # set video
        self.video_quality_select.clear() 
        tmp = sorted(list(resolve_ret['videos'].keys()),reverse=True)
        video_quality = [bilibili_agent2.VIDEO_QUALITY_DICT[x] for x in tmp]
        self.video_quality_select.addItems(video_quality)
        self.video_quality_select.setCurrentIndex(0)
        # set audio
        self.audio_quality_select.clear()
        tmp = [x if x!=30280 else 30249 for x in list(resolve_ret['audios'].keys())]
        tmp = sorted(tmp, reverse=True)
        audio_quality = [bilibili_agent2.AUDIO_QUALITY_DICT[x] for x in tmp]
        self.audio_quality_select.addItems(audio_quality)
        self.audio_quality_select.setCurrentIndex(0)
    
    def _video_quality_change(self):
        current_quality = bilibili_agent2.VIDEO_QUALITY_DICT_T[self.video_quality_select.currentText()]
        if current_quality != '':
            self.video_codec_select.clear()
            codec_list = sorted(list(self.resolve_ret['videos'][current_quality].keys()))
            codec_list = [bilibili_agent2.CODEC_DICT[x] for x in codec_list]
            self.video_codec_select.addItems(codec_list)

    def _login_event(self):
        text = self.login_button.text()
        if text == '注销':
            self.agent.logout()
            self._update_login() 
        elif text == '扫码登录':
            self.qrwindow = MyQRWindow(self, self.agent)
            self.qrwindow.finish.connect(self._update_login)
            self.qrwindow.show()
    
    def _bv_resolve_event(self):
        bv_or_url = self.bv_input.text()
        check, ret = self.agent.get_info(bv_or_url, True)
        if check:
            self._set_widgets(ret)
    
    def _select_save_path_event(self):
        filepath = QFileDialog.getExistingDirectory(self.central_widget,dir=bilibili_agent2.USER_PATH)
        if filepath != "":
            self.save_path_display.setText(filepath)

    def _download_event(self):
        # get video info
        video_quality = bilibili_agent2.VIDEO_QUALITY_DICT_T[self.video_quality_select.currentText()]
        video_codec = bilibili_agent2.CODEC_DICT_T[self.video_codec_select.currentText()]
        video = self.resolve_ret['videos'][video_quality][video_codec][0]
        # get audio
        audio_quality = bilibili_agent2.AUDIO_QUALITY_DICT_T[self.audio_quality_select.currentText()]
        audio = self.resolve_ret['audios'][audio_quality][0]
        # get path
        save_path = self.save_path_display.text()
        # get save audio
        save_audio = self.audio_save_box.isChecked()
        p = Thread(target=self.agent.download,args=(video, audio, save_audio, save_path))
        p.daemon = True 
        p.start()
        # self.agent.download(video, audio, save_path)

    def _write_log_info(self, text: str):
        log_cursor = self.log_display.textCursor()
        log_cursor.movePosition(QTextCursor.End)
        log_cursor.insertText(text)
        self.log_display.setTextCursor(log_cursor)
        self.log_display.ensureCursorVisible()
    
class MyQRWindow(QMainWindow):
    finish = Signal()
    def __init__(self, parent:QMainWindow, agent:bilibili_agent2.BilibiliAgent):
        super().__init__(parent)
        self.setWindowTitle('b站扫码登陆')
        self.setFixedSize(250,250)
        x = parent.x()
        y = parent.y()
        self.move(x + 80, y + 45)
        icon = QIcon()
        icon.addFile(os.path.join(bilibili_agent2.ROOT_PATH, "resources", "icons", "bilibili.png"))
        self.setWindowIcon(icon)
        self.setWindowModality(Qt.ApplicationModal)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.agent = agent
        self._init_ui()
        self._init_connect()
        self._init_scan_thread()
    
    def _init_ui(self):
        # qr img
        self.qr_img = QLabel(self.central_widget)
        # self.agent.get_qrcode()
        # img = QImage(bilibili_agent2.QR_IMG).scaled(QSize(250,250), aspectMode=Qt.KeepAspectRatio)
        # img = QImage.convertToFormat(img, QImage.Format_ARGB32)
        # p = QPainter()
        # p.begin(img)
        # p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        # p.fillRect(img.rect(), QColor(0,0,0,100))
        # p.end()
        pixmap = QPixmap(QSize(255,255))
        pixmap.fill(QColor(255,255,255))
        self.qr_img.setPixmap(pixmap)

        # refresh button
        self.refresh_button = QPushButton(self.central_widget)
        self.refresh_button.move(100,100)
        self.refresh_button_icon = QIcon(QPixmap(os.path.join(bilibili_agent2.ROOT_PATH, "resources", "icons", "refresh.png")).scaled(QSize(50,50), aspectMode=Qt.KeepAspectRatio))
        self.refresh_button.setFixedSize(50,50)
        self.refresh_button.setIcon(self.refresh_button_icon)
        self.refresh_button.setVisible(False)

        # complete img
        self.complete_img = QLabel(self.central_widget)
        self.complete_img.move(100,100)
        self.complete_piximg = QPixmap(os.path.join(bilibili_agent2.ROOT_PATH, "resources", "icons", "complete.png")).scaled(QSize(50,50), aspectMode=Qt.KeepAspectRatio)
        self.complete_img.setPixmap(self.complete_piximg)
        self.complete_img.setVisible(False)
    
    def _init_connect(self):
        self.refresh_button.clicked.connect(self.agent.get_qrcode)

    def _init_scan_thread(self):
        self._scan_thread = QThread(self)
        self._scan_worker = ScanWorker(self.agent)
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_worker.scan_state_changed.connect(self._change_ui)
        self._scan_thread.started.connect(self._scan_worker.login_run)
        self._scan_thread.start()
    
    def _change_ui(self, state: int):
        if state == 1:
            self.complete_img.setVisible(False)
            self.refresh_button.setVisible(False)
            self.qr_pixmap = QPixmap(bilibili_agent2.QR_IMG).scaled(QSize(250,250), aspectMode=Qt.KeepAspectRatio)
            self.qr_img.setPixmap(self.qr_pixmap)
        elif state == 2:
            self.complete_img.setVisible(True)
            self.refresh_button.setVisible(False)
            img = QImage(bilibili_agent2.QR_IMG).scaled(QSize(250,250), aspectMode=Qt.KeepAspectRatio)
            img = QImage.convertToFormat(img, QImage.Format_ARGB32)
            p = QPainter()
            p.begin(img)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(img.rect(), QColor(0,0,0,100))
            p.end()
            self.qr_pixmap =QPixmap.fromImage(img, flags=Qt.NoFormatConversion)
            self.qr_img.setPixmap(self.qr_pixmap)
        elif state == 3:
            self.complete_img.setVisible(False)
            self.refresh_button.setVisible(True)
            img = QImage(bilibili_agent2.QR_IMG).scaled(QSize(250,250), aspectMode=Qt.KeepAspectRatio)
            img = QImage.convertToFormat(img, QImage.Format_ARGB32)
            p = QPainter()
            p.begin(img)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(img.rect(), QColor(0,0,0,100))
            p.end()
            self.qr_pixmap =QPixmap.fromImage(img, flags=Qt.NoFormatConversion)
            self.qr_img.setPixmap(self.qr_pixmap)
        else:
            self.close()
        
    def closeEvent(self, event: QCloseEvent) -> None:
        self._scan_worker.end_scan()
        self._scan_thread.quit()
        self.finish.emit()
        return super().closeEvent(event)

class ScanWorker(QObject):
    scan_state_changed = Signal(int)

    def __init__(self, agent: bilibili_agent2.BilibiliAgent) -> None:
        super().__init__()
        self.agent = agent
        self._init_state()
    
    def login_run(self):
        self.agent.get_qrcode()
        self._update_state(self.agent.scan_state)
        while self._runing:
            if self._end:
                break
            time.sleep(2)
            self.agent.get_scan_ret()
            self._update_state(self.agent.scan_state)

    def end_scan(self):
        self._end = True

    def _update_state(self, state: int):
        if state != self._state:
            self.scan_state_changed.emit(state)
            self._state = state
            if self._runing and state == 10:
                self._runing = False
            elif not self._runing:
                self._runing =True

    def _init_state(self):
        self._state = 0
        self._runing = False
        self._end = False

class Stream(QObject):
    stream_update = Signal(str)

    def write(self, text: str):
        self.stream_update.emit(text)

if __name__ == "__main__":
    # app = QApplication(sys.argv)
    app = QApplication()
    win = MyMainWindow()
    win.show()
    app.exec()