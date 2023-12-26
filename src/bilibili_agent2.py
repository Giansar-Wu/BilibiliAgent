import os
import re
import requests
import html
import json
import datetime
import qrcode
from tqdm import tqdm
import subprocess

PATH = os.path.abspath(os.path.dirname(__file__))
USER_PATH = os.path.expanduser('~')
DEFAULT_OUT_DIR = os.path.join(USER_PATH, 'Desktop', 'Output')
ROOT_PATH = os.path.dirname(PATH)
BIN_PATH = os.path.join(ROOT_PATH, 'bin')
TMP_PATH = os.path.join(ROOT_PATH, 'resources', 'tmp')
DATA_PATH = os.path.join(ROOT_PATH, 'resources', 'data')
QR_IMG = os.path.join(TMP_PATH, 'qrcode.png')
if not os.path.exists(TMP_PATH):
    os.makedirs(TMP_PATH)
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

VIP_TYPE_DICT = {
    0:"会员",
    1:"大会员",
    2:"年度大会员"
}
CODEC_DICT = {
    7:'AVC',
    12:'HEVC',
    13:'AV1'
}
CODEC_DICT_T = {
    'AVC':7,
    'HEVC':12,
    'AV1':13
}
VIDEO_QUALITY_DICT = {
    127:"超高清 8K",
    126:"杜比视界",
    125:"HDR 真彩色",
    120:"超清 4K",
    116:"高帧率 1080P60",
    112:"高码率 1080P+",
    80 :"高清 1080P",
    74 :"高帧率 720P60",
    64 :"高清 720P",
    32 :"清晰 480P",
    16 :"流程 360P",
    6  :"极速240p"
}
VIDEO_QUALITY_DICT_T = {
    "超高清 8K":127,
    "杜比视界":126,
    "HDR 真彩色":125,
    "超清 4K":120,
    "高帧率 1080P60":116,
    "高码率 1080P+":112,
    "高清 1080P":80 ,
    "高帧率 720P60":74 ,
    "高清 720P":64 ,
    "清晰 480P":32 ,
    "流程 360P":16 ,
    "极速240p":6
}
AUDIO_QUALITY_DICT = {
    30216:"64K",
    30232:"132K",
    30280:"192K",
    30249:"192K", # for sort only
    30250:"杜比全景声",
    30251:"Hi-Res无损"
}
AUDIO_QUALITY_DICT_T = {
    "64K":30216,
    "132K":30232,
    "192K":30280,
    "杜比全景声":30250,
    "Hi-Res无损":30251
}

class BilibiliAgent(object):
    def __init__(self) -> None:
        self.scan_state = 0
        self.user_info = {}
        # clean tmp
        self._clean()
        # check cookie
        if os.path.exists(F"{ROOT_PATH}/resources/data/cookie.txt"):
            with open(F"{ROOT_PATH}/resources/data/cookie.txt", "r", encoding="utf-8") as f:
                cookie = f.read()
            self._set_headers(cookie=cookie)
            if not self._get_user_info():
                self.logout()
            else:
                self._login_state = True
        else:
            self._set_headers()
            self._login_state = False
    
    def _set_headers(self, referer: str="https://www.bilibili.com/", cookie: str="") -> None:
        headers = {}
        # headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        # headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
        headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        headers["referer"] = referer
        headers["Cookie"] = cookie
        self.headers = headers
        # print(headers)
    
    def _get_user_info(self):
        url = "https://api.bilibili.com/x/web-interface/nav"
        res = requests.get(url=url, headers=self.headers).text
        res = json.loads(res)
        if res["code"] == 0:
            self.user_info['uname'] = res["data"]["uname"]
            self.user_info['level'] = res["data"]["level_info"]["current_level"]
            self.user_info['vip'] = VIP_TYPE_DICT[res["data"]["vipType"]]
            return True
        elif res["code"] == -101:
            self.user_info = {}
            return False

    def get_login_state(self) -> bool:
        return self._login_state

    def logout(self) -> None:
        if os.path.exists(F"{ROOT_PATH}/resources/data/cookie.txt"):
            os.remove(F"{ROOT_PATH}/resources/data/cookie.txt") 
        self._set_headers()
        self._get_user_info()
        self._login_state = False

    def get_qrcode(self):
        logurl = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        res = requests.get(url=logurl, headers=self.headers).text
        res = json.loads(res)
        qr_img = qrcode.make(res["data"]["url"])
        qr_img.save(QR_IMG)
        self._qrcode_key = res["data"]["qrcode_key"]
        self.get_scan_ret()

    def get_scan_ret(self):
        url = F"https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={self._qrcode_key}"
        res = requests.get(url=url, headers=self.headers)
        res_text = json.loads(res.text)
        message = res_text["data"]["message"]
        code = res_text["data"]["code"]
        if code == 0:
            cookie = res.headers["Set-Cookie"]
            with open(F"{ROOT_PATH}/resources/data/cookie.txt", "w", encoding="utf-8") as f:
                f.write(cookie)
            self.scan_state = 10
            self._set_headers(cookie=cookie)
            self._get_user_info()
            self._login_state = True
        elif code == 86101:
            self.scan_state = 1
            self._login_state = False
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}!")
        elif code == 86090:
            self.scan_state = 2
            self._login_state = False
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}!")
        elif code == 86038:
            self.scan_state = 3
            self._login_state = False
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}!")
    
    def get_info(self,bv_or_url: str, debug: bool) -> (bool, dict):
        """200 success
            101 bv error
            102 title error

        Args:
            self (): _description_
            dict (_type_): _description_

        Returns:
            _type_: _description_
        """
        ret = {}
        ret['code'] = 200

        # get bv
        bv = re.findall(r"[bB][vV][0-9a-zA-Z]{10}", bv_or_url)
        if len(bv) == 0:
            print(F"请输入正确的BV号或者https链接！")
            ret['code'] = 101
            return False, ret
        ret['bv'] = bv[0]

        web_res = requests.get(url=F"https://www.bilibili.com/video/{ret['bv']}/", headers=self.headers)
        web_res = html.unescape(web_res.text)
        if debug:
            with open(os.path.join(TMP_PATH, F"{ret['bv']}.html"), 'w', encoding='utf-8') as f:
                f.write(web_res)

        # get title
        title = re.findall(r"<h1.*>(.*?)</h1>", web_res)
        if len(title) == 0:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 链接无效!")
            ret['code'] = 102
            return False, ret
        ret['title'] = self._filename_invalid_character_replace(title[0])

        # get resource info
        resource_info = re.findall(r"(?<=<script>window.__playinfo__=).*?(?=</script>)", web_res)
        if len(resource_info) == 0:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 解析失败!")
            ret['code'] = 103
            return False, ret
        resource_info = json.loads(resource_info[0])
        if debug:
            with open(os.path.join(TMP_PATH, F"{ret['title']}.json"), 'w', encoding='utf-8') as f:
                json.dump(resource_info, f, ensure_ascii=False)

        # video resolve
        videos = {}
        for unit_info in resource_info['data']['dash']['video']:
            quality = unit_info['id']
            codec = unit_info['codecid']
            if quality not in videos.keys():
                videos[quality] = {}
            if codec not in videos[quality].keys():
                videos[quality][codec] = []
            tmp = {}
            tmp['title'] = ret['title']
            tmp['url'] = unit_info['backup_url'][0]
            tmp['bandwidth'] = unit_info['bandwidth']
            tmp['resolution'] = F"{unit_info['width']}×{unit_info['height']}"
            tmp['framerate'] = unit_info['frame_rate']
            videos[quality][codec].append(tmp)
        if len(videos) == 0:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 无视频源!")
            ret['code'] = 104
            return False, ret
        ret['videos'] = videos

        # audio resolve
        audios = {}
        for unit_info in resource_info['data']['dash']['audio']:
            quality = unit_info['id']
            if quality not in audios.keys():
                audios[quality] = []
            tmp = {}
            tmp['title'] = ret['title']
            tmp['url'] = unit_info['backup_url'][0]
            tmp['bandwidth'] = unit_info['bandwidth']
            tmp['suffix'] = 'm4a'
            audios[quality].append(tmp)
        # resolve flac
        if 'flac' in resource_info['data']['dash'].keys() and resource_info['data']['dash']['flac'] and resource_info['data']['dash']['flac']['audio']:
            unit_info = resource_info['data']['dash']['flac']['audio']
            quality = unit_info['id']
            if quality not in audios.keys():
                audios[quality] = []
            tmp = {}
            tmp['title'] = ret['title']
            tmp['url'] = unit_info['backup_url'][0]
            tmp['bandwidth'] = unit_info['bandwidth']
            tmp['suffix'] = 'flac'
            audios[quality].append(tmp)
        # resolve dolby
        if 'dolby' in resource_info['data']['dash'].keys() and resource_info['data']['dash']['dolby'] and resource_info['data']['dash']['dolby']['audio']:
            unit_info = resource_info['data']['dash']['dolby']['audio']
            quality = unit_info['id']
            if quality not in audios.keys():
                audios[quality] = []
            tmp = {}
            tmp['title'] = ret['title']
            tmp['url'] = unit_info['backup_url'][0]
            tmp['bandwidth'] = unit_info['bandwidth']
            tmp['suffix'] = 'ec3'
            audios[quality].append(tmp)
        if len(audios) == 0:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 无音频源!")
            ret['code'] = 105
            return False, ret
        ret['audios'] = audios
        return True, ret
    
    def download(self, video: dict, audio: dict, save_audio, out_path: str=DEFAULT_OUT_DIR) -> None:
        # download video
        video_url = video['url']
        video_filename = F"{video['title']}.mp4"
        self._download_unit(video_url, TMP_PATH, video_filename, 'Video')
        # download audio
        audio_url = audio['url']
        audio_filename = F"{audio['title']}.{audio['suffix']}"
        self._download_unit(audio_url, TMP_PATH, audio_filename, 'Audio')
        if os.path.splitext(audio_filename)[-1] == '.flac':
            out_filename = F"{video['title']}.mkv"
        else:
            out_filename = F"{video['title']}.mp4"
        self._output_video(video_filename, audio_filename, out_path, out_filename, save_audio)

    def _download_unit(self, url: str, path: str, filename: str, category: str) -> None:
        with requests.get(url=url, headers=self.headers, stream=True) as resp:
            # type of headers:requests.structures.CaseInsensitiveDict(一种不区分大小写的字典)
            total = int(resp.headers.get('content-length', 0))
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {category} download started:")
            with open(os.path.join(path, filename), 'wb') as file, tqdm(desc=category, total=total, ncols=100, mininterval = 0.3, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {category} download accomplished!")
    
    def _output_video(self, video_name: str, audio_name: str, out_path: str, out_filename: str, save_audio: bool) -> None:
        ffmpeg = os.path.join(BIN_PATH, 'ffmpeg.exe')
        # loglevel:'quiet, info, debug
        loglevel = 'quiet'
        video_file = os.path.join(TMP_PATH, video_name)
        audio_file = os.path.join(TMP_PATH, audio_name)
        out_file = os.path.join(out_path, out_filename)
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Combining...")
        subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {video_file} -i {audio_file} -vcodec copy -acodec copy -map_metadata -1 {out_file}", shell=True)
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Combiantion accomplished!")
        if save_audio:
            if audio_name.split('.')[-1] == 'ec3':
                audio_out = os.path.join(out_path, F"{audio_name.split('.')[0]}.mp4")
            else:
                audio_out = os.path.join(out_path, audio_name)
            subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {audio_file} -acodec copy -map_metadata -1 {audio_out}", shell=True)

    def _clean(self) -> None:
        for root, dirs, files in os.walk(TMP_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def _filename_invalid_character_replace(self, s: str) -> str:
        Filename_Invalid_Character = ('<', '>', '/', '\\', '|', ':', '*', '?','"', ' ')
        for character in Filename_Invalid_Character:
            s = s.replace(character, "_")
        return s