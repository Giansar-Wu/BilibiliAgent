import re
import os
import subprocess
import threading
import tkinter
import json
import time
import html
import requests
import qrcode
import numpy as np


from queue import Queue
from typing import Callable
from PIL import Image,ImageTk
from tqdm import tqdm

PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.dirname(PATH)
BIN_PATH = os.path.join(ROOT_PATH, 'bin')
TMP_PATH = os.path.join(ROOT_PATH, 'resources', 'tmp')
# QR_IMG = F"{ROOT_PATH}/resources/data/qrcode.png"
# QR_IMG = F"{os.path.expanduser('~')}/qrcode.png"
QR_IMG = os.path.join(TMP_PATH, 'qrcode.png')
CODECS_DICT={
    'avc1':'AVC',
    'hvc1':'HEVC',
    'hev1':'HEVC',
    'dvh1':'HEVC',
    'av01':'AV1'
}

class ScanWindow(object):
    def __init__(self, width: int=250) -> None:
        self.__qr_width = width

        # start a window and set the window's title and icon
        self.__window = tkinter.Tk()
        self.__window.title ("扫码登陆")
        # self.__window.iconbitmap(F"{ROOT_PATH}/resources/icons/bilibili.svg")
        self.__window.iconphoto(True, tkinter.PhotoImage(file=F"{ROOT_PATH}/resources/icons/bilibili.png"))

        # set the window's prompt words
        self.__title = tkinter.Label(self.__window, text="请使用 bilibili 客户端扫码登陆", bg="white", fg="#fb7299", font=("微软雅黑", 22), wraplength=width)
        self.__title.grid(row=0, column=0, sticky="nwe")

        # set a display zone for QR code
        self.__qrcode_img = ImageTk.PhotoImage(Image.new('RGB', (width, width), (255, 255, 255)))
        self.__qrcode_display = tkinter.Label(self.__window, image=self.__qrcode_img, bg="white")
        self.__qrcode_display.grid(row=1, column=0, sticky="swe")

        # set a icon for displaying after the QR code is scanned
        scaned_img = Image.open(F"{ROOT_PATH}/resources/icons/complete.png")
        self.__scanned_icon = ImageTk.PhotoImage(scaned_img.resize((int(width / 3), int(width / 3))))
        self.__scanned_label = tkinter.Label(self.__window, image=self.__scanned_icon)
        self.__scanned_label.grid(row=1, column=0)
        self.__scanned_label.grid_remove()

        # set a refresh button
        refresh_img = Image.open(F"{ROOT_PATH}/resources/icons/refresh.png")
        self.__refresh_icon = ImageTk.PhotoImage(refresh_img.resize((40,40)))
        self.__refresh_button = tkinter.Button(self.__window, text="点击刷新", bg="white", fg="#87CEFA", font=("微软雅黑", 20), image=self.__refresh_icon, relief="flat", compound='top', command=self.__refresh)
        self.__refresh_button.grid(row=1, column=0)
        self.__refresh_button.grid_remove()

        # set the window's size
        self.__window.geometry('+-3000+-3000')
        self.__window.update()
        sw = self.__window.winfo_screenwidth()
        sh = self.__window.winfo_screenheight()
        w = self.__qrcode_display.winfo_width()
        h = w + self.__title.winfo_height()
        x, y = int(sw / 2 - w / 2), int(sh / 2 - h / 2)

        self.__window.geometry(F"{w}x{h}+{x}+{y}")
        self.__window.resizable(width=False,height=False)
        self.__window.protocol("WM_DELETE_WINDOW", self.__quit)

    def run(self, q_receive: Queue, q_send: Queue, t: int=100):
        self.q_send = q_send
        self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
        self.__window.mainloop()

    def __loop(self, t: int, q_receive: Queue):
        if q_receive.empty():
            self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
        else:
            signal_ = q_receive.get()
            if signal_ == 0:
                self.__update_img()
                self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
            elif signal_ == 1:
                self.__scaned()
                self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
            elif signal_ == 2:
                self.__overdue()
                self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
            elif signal_ == 3:
                self.__scaned_overdue()
                self.__after_id = self.__window.after(t, self.__loop, t, q_receive)
            elif signal_ == 4:
                self.__window.destroy()

    def __quit(self):
        self.__window.after_cancel(self.__after_id)
        self.__window.destroy()

    def __scaned(self):
        img = Image.open(QR_IMG)
        array = np.array(img, dtype=np.float64)
        array = (array / 2 + 0.5) * 255
        img = Image.fromarray(array)
        self.__qrcode_img = ImageTk.PhotoImage(img.resize((self.__qr_width, self.__qr_width)))
        self.__qrcode_display.configure(image=self.__qrcode_img)
        self.__scanned_label.grid()

    def __overdue(self):
        img = Image.open(QR_IMG)
        array = np.array(img, dtype=np.float64)
        array = (array / 2 + 0.5) * 255
        img = Image.fromarray(array)
        self.__qrcode_img = ImageTk.PhotoImage(img.resize((self.__qr_width, self.__qr_width)))
        self.__qrcode_display.configure(image=self.__qrcode_img)
        self.__refresh_button.grid()

    def __scaned_overdue(self):
        self.__scanned_label.grid_remove()
        self.__refresh_button.grid()

    def __refresh(self):
        self.q_send.put(1)
        self.__qrcode_img = ImageTk.PhotoImage(Image.new('RGB', (self.__qr_width,self.__qr_width), (255, 255, 255)))
        self.__qrcode_display.configure(image=self.__qrcode_img)
        self.__refresh_button.grid_remove()

    def __update_img(self):
        img = Image.open(QR_IMG)
        self.__qrcode_img = ImageTk.PhotoImage(img.resize((self.__qr_width, self.__qr_width)))
        self.__qrcode_display.configure(image=self.__qrcode_img)

class MyThread(threading.Thread):
    def __init__(self, target: Callable, args) -> None:
        super().__init__()
        self.__func = target
        self.__args = args
        # self.__ret = None

    def run(self):
        self.__ret = self.__func(*self.__args)

    def get_ret(self):
        return self.__ret

class BilibiliAgent(object):
    def __init__(self) -> None:
        self.__clean()
        self.set_headers()
        self.setting()
        if os.path.exists(F"{ROOT_PATH}/resources/data/cookie.txt"):
            with open(F"{ROOT_PATH}/resources/data/cookie.txt", "r", encoding="utf-8") as f:
                cookie = f.read()
            self.set_headers(cookie=cookie)
            self.__logged_in = True
        else:
            self.__logged_in, cookie = self.login()
            self.set_headers(cookie=cookie)
        if self.__logged_in:
            print("账号已登录!")
        else:
            print("账号未登录!")

    def setting(self):
        config = os.path.join(ROOT_PATH, 'config.json')
        if os.path.exists(config):
            with open(config, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            self.video_path = os.path.abspath(config_dict['video_path'])
            self.save_audio = config_dict['save_audio']
            if self.save_audio:
                self.audio_path = os.path.abspath(config_dict['audio_path'])

    def set_headers(self, referer: str="https://www.bilibili.com/", cookie: str=""):
        headers = {}
        # headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
        headers["referer"] = referer
        headers['Cookie'] = cookie
        self.headers = headers
        # print(headers)

    def login(self):
        """Login bilibili by scanning qrcode and get cookies.

        Args:

        Returns:
            A binary tuple which has a bool value as login state and a string as cookie. If the login state is False, the cookie is usually a blank string.
            example:
                (False, "")

        """
        q1 = Queue()
        q2 = Queue(2)
        self.scan_window = ScanWindow()
        listening = MyThread(target=self.__listening, args=(q1, q2))
        listening.setDaemon(True)
        listening.start()
        self.scan_window.run(q_receive=q1, q_send=q2, t=100)
        q2.put(0)
        listening.join()
        ret_code, cookie = listening.get_ret()
        if ret_code == 3:
            return True, cookie
        else:
            print("登陆已取消!")
            return False, cookie

    def __listening(self, q_send: Queue, q_receive: Queue):
        state = 0
        last_state = 0
        cookie = ""
        qrcode_url, qrcode_key = self.__get_qrcode_url_key()
        self.__get_qrcode_img(qrcode_url)
        q_send.put(0)
        while q_receive.empty():
            time.sleep(3)
            if not q_receive.empty():
                break
            ret_message, cookie = self.__get_ret(qrcode_key)
            print(ret_message)
            if ret_message == "未扫码":
                last_state = state
                state = 0
            elif ret_message == "二维码已扫码未确认":
                last_state = state
                state = 1
                if last_state == 0:
                    q_send.put(1)
            elif ret_message == "二维码已失效":
                last_state = state
                state = 2
                if last_state == 0:
                    q_send.put(2)
                elif last_state == 1:
                    q_send.put(3)
                while q_receive.empty():
                    pass
                signal_ = q_receive.get()
                if signal_ == 0:
                    break
                elif signal_ == 1:
                    qrcode_url, qrcode_key = self.__get_qrcode_url_key()
                    self.__get_qrcode_img(qrcode_url)
                    q_send.put(0)
            else:
                last_state = state
                state = 3
                q_send.put(4)
                break
        os.remove(QR_IMG)
        return state, cookie

    def __get_qrcode_url_key(self):
        logurl = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate?source=main-web"
        res = requests.get(url=logurl, headers=self.headers).text
        res = json.loads(res)
        return res["data"]["url"], res["data"]["qrcode_key"]

    def __get_qrcode_img(self, content: str):
        qr_img = qrcode.make(content)
        qr_img.save(QR_IMG)

    def __get_ret(self, qrcode_key):
        url = F"https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}"
        res = requests.get(url=url, headers=self.headers)
        res_text = json.loads(res.text)
        cookie = ""
        message = res_text["data"]["message"]
        if not message:
            cookie = res.headers["Set-Cookie"]
            with open(F"{ROOT_PATH}/resources/data/cookie.txt", "w", encoding="utf-8") as f:
                f.write(cookie)
        return message, cookie

    def download(self, bv_or_url: str, debug: bool=True):
        """Download from bilibili web.

        Args:
            bv_or_url: str. The bv number or the url of the video.
            video_path: str, default "downloaded_videos". The path to save videos.
            save_audio: bool, default False. Whether to save audio files.
            audio_path: str, default "". This value is only valid when save_audio is True. The path to save audios. If it is None, the audio_path will be same as path.
            aompatible: bool, default False. If the value is True, it will preferentially download videos encoded with "avc/h.264" codec. Otherwise, it will preferentially download videos encoded with "hevc/h.265" codec.
            debug: bool, default False. Whether to use debug mode.

        Returns:
            None
        """
        if len(bv_or_url) == 12 and bv_or_url[0:2].lower() == 'bv' and bv_or_url.isalnum():
            web_res = requests.get(url=F"https://www.bilibili.com/{bv_or_url}", headers=self.headers)
        elif bv_or_url[0:8].lower() =='https://':
            web_res = requests.get(url=bv_or_url, headers=self.headers)
        else:
            print(F"请输入正确的BV号或者https链接！")
            return 1
        if web_res.status_code != 200:
            print(F"链接出错，错误代码:{web_res.status_code}")
            return web_res.status_code
        web_res = html.unescape(web_res.text)
        with open(os.path.join(ROOT_PATH, 'resources', 'data', F'page.html'), 'w', encoding='utf-8') as f:
            f.write(web_res)
        # get brief title
        title = None
        title_re_list=[r'<title data-vue-meta="true">(.*?)</title>', r'<title>(.*?)</title>']
        title_suffix_list=["_哔哩哔哩_bilibili", "_哔哩哔哩bilibili", "-bilibili-哔哩哔哩", "-番剧-高清独家在线观看"]
        for tmp in title_re_list:
            if not title:
                title = re.findall(tmp, web_res)
        if not title:
            print(F"标题解析失败或当且页面还不支持下载！")
            return 2
        else:
            title = title[0]
            for suffix in title_suffix_list:
                title = title.replace(suffix, "")
        # print(title)
        if title == "视频去哪了呢？":
            print(F"视频已下架或BV号、链接输入有误!请检查输入的BV号或链接。")
            return 3
        title = self.__character_replace(title)
        # get resource information
        resource_info = re.findall(r"<script>window.__playinfo__=(.*?)</script>", web_res)
        if not resource_info:
            print("请确认输入的是否是B站视频的链接!暂不支持其他网站!")
            return 4
        else:
            resource_info = resource_info[0]
        resource_info = json.loads(resource_info)
        # debug
        # if debug and not os.path.exists(os.path.join(ROOT_PATH, 'resources', 'data', F"{title}.json")):
        if debug:
            with open(os.path.join(ROOT_PATH, 'resources', 'data', F"{title}.json"), 'w', encoding='utf-8') as f:
                json.dump(resource_info, f, ensure_ascii=False)
        # get video's url
        video_filename = self.__download_video(resource_info["data"], title)
        # get audio
        audio_filename = self.__download_audio(resource_info["data"]["dash"], title)
        # return 0
        # merge video adn audio
        if os.path.splitext(audio_filename)[-1] == '.flac':
            output_name = F"{title}.mkv"
        else:
            output_name = F"{title}.mp4"
        self.__output_video(video_name=video_filename, audio_name=audio_filename, output_name=output_name)

    def __character_replace(self, s: str):
        ret = []
        for char in s:
            ret.append(self.__Q2B(char))
        ret = ''.join(ret)
        Filename_Invalid_Character = ('<', '>', '/', '\\', '|', ':', '*', '?', ' ')
        for character in Filename_Invalid_Character:
            ret = ret.replace(character, "_")
        return ret

    def __Q2B(self, uchar):
        """单个字符 全角转半角"""
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
            return uchar
        return chr(inside_code)

    def __download_video(self, data: dict, title: str):
        video_dict = {}
        for item in data['dash']['video']:
            quality = item['id']
            if quality not in video_dict:
                video_dict[quality] = {}
            codec = item['codecs'].split('.')[0]
            video_dict[quality][codec] = [item['backup_url'][0], item['bandwidth'], F"{item['width']}×{item['height']}",item['frameRate']]
        video_select_quality = video_dict[max(video_dict.keys())]
        priority_dict = {'HEVC':1, 'AV1':2, 'AVC':3}
        video_select_quality_sorted = {}
        for codec in video_select_quality.keys():
            if codec not in CODECS_DICT:
                print(F"编解码器{codec}不在已知列表中！")
            else:
                id_ = priority_dict[CODECS_DICT[codec]]
                video_select_quality_sorted[id_] = video_select_quality[codec]
                video_select_quality_sorted[id_].append(CODECS_DICT[codec])
        video_ = video_select_quality_sorted[max(video_select_quality_sorted.keys())]
        video_url = video_[0]
        #download video
        filename = F"{title}.mp4"
        print(F"视频:{filename}:\n码率:{video_[1] / (1024*1024):.2f}Mbps\n分辨率:{video_[2]}\n帧率:{video_[3]}\n编码:{video_[4]}")
        self.__download(url=video_url, filename=filename)
        return filename

    def __download_audio(self, data_dash: dict, title: str):
        # get audio's url
        audio_url_dict = {}
        for data in data_dash['audio']:
            bandwidth = data['bandwidth']
            audio_url_dict[bandwidth] = (data['backup_url'][0], 'm4a')
        if 'flac' in data_dash.keys():
            if data_dash['flac']:
                if data_dash['flac']['audio']:
                    bandwidth = data_dash['flac']['audio']['bandwidth']
                    audio_url_dict[bandwidth] = (data_dash['flac']['audio']['backup_url'][0], 'flac')
        if 'dolby' in data_dash.keys():
            if data_dash['dolby']:
                if data_dash['dolby']['audio']:
                    bandwidth = data_dash['dolby']['audio'][0]['bandwidth']
                    audio_url_dict[bandwidth] = (data_dash['dolby']['audio'][0]['backup_url'][0], 'ec3')
        bandwidth = max(audio_url_dict.keys())
        audio_url = audio_url_dict[bandwidth][0]
        audio_suffix = audio_url_dict[bandwidth][1]
        # download audio
        filename = F"{title}.{audio_suffix}"
        print(F"音频:{filename}\n码率:{bandwidth / 1024:.2f}Kbps")
        self.__download(url=audio_url, filename=filename)
        return filename

    def __download(self, url: str, filename: str):
        with requests.get(url=url, headers=self.headers, stream=True) as resp:
            # type of headers:requests.structures.CaseInsensitiveDict(一种不区分大小写的字典)
            total = int(resp.headers.get('content-length', 0))
            print(F"下载中...")
            with open(os.path.join(TMP_PATH, filename), 'wb') as file, tqdm(total=total, ncols=100, unit='iB', unit_scale=True,unit_divisor=1024) as bar:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
            print(F"下载完成")

    def __output_video(self, video_name: str, audio_name: str, output_name: str):
        ffmpeg = os.path.join(BIN_PATH, 'ffmpeg.exe')
        # loglevel:'quiet, info, debug
        loglevel = 'quiet'
        video_file = os.path.join(TMP_PATH, video_name)
        audio_file = os.path.join(TMP_PATH, audio_name)
        out_file = os.path.join(self.video_path, output_name)
        print("Combining...")
        subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {video_file} -i {audio_file} -vcodec copy -acodec copy -map_metadata -1 {out_file}", shell=True)
        print("Combiantion accomplished!")
        self.save_audio = True
        if self.save_audio:
            if audio_name.split('.')[-1] == 'ec3':
                audio_out = os.path.join(self.audio_path, F"{audio_name.split('.')[0]}.mp4")
            else:
                audio_out = os.path.join(self.audio_path, audio_name)
            subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {audio_file} -acodec copy -map_metadata -1 {audio_out}", shell=True)

    def __clean(self):
        for root, dirs, files in os.walk(TMP_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

if __name__ == "__main__":
    agent = BilibiliAgent()
    url=input("url:")
    agent.download(url)