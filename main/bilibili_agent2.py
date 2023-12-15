import os
import re
import requests
import html
import json
from tqdm import tqdm
import subprocess

PATH = os.path.abspath(os.path.dirname(__file__))
USER_PATH = os.path.expanduser('~')
DEFAULT_OUT_DIR = os.path.join(USER_PATH, 'Desktop', 'Output')
ROOT_PATH = os.path.dirname(PATH)
BIN_PATH = os.path.join(ROOT_PATH, 'bin')
TMP_PATH = os.path.join(ROOT_PATH, 'resources', 'tmp')
CODEC_DICT = {
    7:'AVC',
    12:'HEVC',
    13:'AV1'
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
AUDIO_QUALITY_DICT = {
    30216:"64K",
    30232:"132K",
    30280:"192K",
    30250:"杜比全景声",
    30251:"Hi-Res无损"
}

class BilibiliAgent(object):
    def __init__(self) -> None:
        self.set_headers()
        self._clean()
        pass

    def set_headers(self, referer: str="https://www.bilibili.com/", cookie: str=""):
        headers = {}
        # headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
        headers["referer"] = referer
        headers['Cookie'] = cookie
        self.headers = headers
        # print(headers)
    
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

        web_res = requests.get(url=F"https://www.bilibili.com/video/{ret['bv']}", headers=self.headers)
        web_res = html.unescape(web_res.text)
        if debug:
            with open(os.path.join(TMP_PATH, F"{ret['bv']}.html"), 'w', encoding='utf-8') as f:
                f.write(web_res)

        # get title
        title = re.findall(r"<h1.*>(.*?)</h1>", web_res)
        if len(title) == 0:
            print(F"链接无效！")
            ret['code'] = 102
            return False, ret
        ret['title'] = self._filename_invalid_character_replace(title[0])

        # get resource info
        resource_info = re.findall(r"(?<=<script>window.__playinfo__=).*?(?=</script>)", web_res)
        if len(resource_info) == 0:
            print(F"解析失败:")
            ret['code'] = 103
            return False, ret
        resource_info = json.loads(resource_info[0])
        if debug:
            with open(os.path.join(TMP_PATH, F"{ret['title']}.json"), 'w', encoding='utf-8') as f:
                json.dump(resource_info, f, ensure_ascii=False)

        # video resolve
        videos = {}
        for unit_info in resource_info['data']['dash']['video']:
            quality = VIDEO_QUALITY_DICT[unit_info['id']]
            codec = CODEC_DICT[unit_info['codecid']]
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
            print(F"无视频源！")
            ret['code'] = 104
            return False, ret
        ret['videos'] = videos

        # audio resolve
        audios = {}
        for unit_info in resource_info['data']['dash']['audio']:
            quality = AUDIO_QUALITY_DICT[unit_info['id']]
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
            quality = AUDIO_QUALITY_DICT[unit_info['id']]
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
            quality = AUDIO_QUALITY_DICT[unit_info['id']]
            if quality not in audios.keys():
                audios[quality] = []
            tmp = {}
            tmp['title'] = ret['title']
            tmp['url'] = unit_info['backup_url'][0]
            tmp['bandwidth'] = unit_info['bandwidth']
            tmp['suffix'] = 'ec3'
            audios[quality].append(tmp)
        if len(audios) == 0:
            print(F"无音频源！")
            ret['code'] = 105
            return False, ret
        ret['audios'] = audios
        return True, ret
    
    def download(self, video: dict, audio: dict, save_audio, out_path: str=DEFAULT_OUT_DIR):
        # download video
        video_url = video['url']
        video_filename = F"{video['title']}.mp4"
        self._download_unit(video_url, TMP_PATH, video_filename)
        # download audio
        audio_url = audio['url']
        audio_filename = F"{audio['title']}.{audio['suffix']}"
        self._download_unit(audio_url, TMP_PATH, audio_filename)
        if os.path.splitext(audio_filename)[-1] == '.flac':
            out_filename = F"{video['title']}.mkv"
        else:
            out_filename = F"{video['title']}.mp4"
        self._output_video(video_filename, audio_filename, out_path, out_filename, save_audio)

    def _download_unit(self, url: str, path: str, filename: str):
        with requests.get(url=url, headers=self.headers, stream=True) as resp:
            # type of headers:requests.structures.CaseInsensitiveDict(一种不区分大小写的字典)
            total = int(resp.headers.get('content-length', 0))
            print(F"下载中...")
            with open(os.path.join(path, filename), 'wb') as file, tqdm(total=total, ncols=100, unit='iB', unit_scale=True,unit_divisor=1024) as bar:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
            print(F"下载完成")
    
    def _output_video(self, video_name: str, audio_name: str, out_path: str, out_filename: str, save_audio: bool):
        ffmpeg = os.path.join(BIN_PATH, 'ffmpeg.exe')
        # loglevel:'quiet, info, debug
        loglevel = 'quiet'
        video_file = os.path.join(TMP_PATH, video_name)
        audio_file = os.path.join(TMP_PATH, audio_name)
        out_file = os.path.join(out_path, out_filename)
        print("Combining...")
        subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {video_file} -i {audio_file} -vcodec copy -acodec copy -map_metadata -1 {out_file}", shell=True)
        print("Combiantion accomplished!")
        if save_audio:
            if audio_name.split('.')[-1] == 'ec3':
                audio_out = os.path.join(out_path, F"{audio_name.split('.')[0]}.mp4")
            else:
                audio_out = os.path.join(out_path, audio_name)
            subprocess.run(F"{ffmpeg} -loglevel {loglevel} -y -i {audio_file} -acodec copy -map_metadata -1 {audio_out}", shell=True)

    def _clean(self):
        for root, dirs, files in os.walk(TMP_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def _filename_invalid_character_replace(self, s: str):
        Filename_Invalid_Character = ('<', '>', '/', '\\', '|', ':', '*', '?','"', ' ')
        for character in Filename_Invalid_Character:
            s = s.replace(character, "_")
        return s

if __name__ == '__main__':
    url="https://www.bilibili.com/video/BV1mv4y1y7wG/?spm_id_from=333.337.search-card.all.click&vd_source=c85725ebe09080a8e373b08a2f30e440"
    # url ="https://www.bilibili.com/video/BV1n3h45k1u5/"
    agent = BilibiliAgent()
    agent.get_info(url, True)