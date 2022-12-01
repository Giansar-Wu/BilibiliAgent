import os
import json
import bilibili_agent

PATH = os.path.abspath(os.path.dirname(__file__)).replace('\\','/')
ROOT_PATH = os.path.dirname(PATH)
CONFIG_PATH = F"{ROOT_PATH}/config.json"

def get_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_ = json.load(f)
        config_["video_path"] = config_["video_path"].replace('\\', '/')
        config_["audio_path"] = config_["audio_path"].replace('\\', '/')
        if config_["save_audio"]:
            if not os.path.exists(config_["video_path"]) and os.path.exists(config_["audio_path"]):
                print(F"视频保存路径:{config_['video_path']}不存在,请重新编辑配置文件!")
                return None
            elif os.path.exists(config_["video_path"]) and not os.path.exists(config_["audio_path"]):
                print(F"音频保存路径:{config_['audio_path']}不存在,请重新编辑配置文件!")
                return None
            elif not os.path.exists(config_["video_path"]) and not os.path.exists(config_["audio_path"]):
                print(F"视频保存路径:{config_['video_path']}不存在,请重新编辑配置文件!")
                print(F"音频保存路径:{config_['audio_path']}不存在,请重新编辑配置文件!")
                return None
        else:
            if not os.path.exists(config_["video_path"]) and os.path.exists(config_["audio_path"]):
                print(F"视频保存路径:{config_['video_path']}不存在,请重新编辑配置文件!")
                return None

        print("已加载配置文件!")
        print(F"视频保存路径为:{config_['video_path']}")
        if config_["save_audio"]:
            if config_["audio_path"]:
                print(F"音频保存路径为:{config_['audio_path']}")
            else:
                print(F"音频保存路径为:{config_['video_path']}")
        return config_
    else:
        print("未找到配置文件,请进行初始化配置!")
        config_ = {}
        while True:
            path = input(F"请输入保存视频的路径:")
            path = path.replace("\\", '/')
            if os.path.exists(path):
                config_["video_path"] = path
                break
            else:
                print("路径不存在,请重新输入!")
        while True:
            tmp = input(F"是否保存音频文件(保存请输入true,不保存直接回车):")
            if tmp == "":
                config_["save_audio"] = False
                config_["audio_path"] = ""
                break
            elif tmp == "true":
                config_["save_audio"] = True
                while True:
                    path = input(F"请输入保存音频的路径(默认为视频保存路径):")
                    path = path.replace("\\", '/')
                    if path == "":
                        path = config_["path"]
                    if os.path.exists(path):
                        config_["audio_path"] = path
                        break
                    else:
                        print("路径不存在请重新输入!")
                break
            else:
                print("输入无法识别,请重新输入!")
        # while True:
        #     tmp = input("是否启用兼容模式(兼容模式默认保存h.264编码的视频, 如需启用请输入true,不启用直接回车):")
        #     if tmp == "":
        #         config_["compatible"] = False
        #         break
        #     elif tmp == "true":
        #         config_["compatible"] = True
        #         break
        #     else:
        #         print("输入无法识别,请重新输入!")
        config_["compatible"] = False
        config_["debug"] = False
        with open(F"{CONFIG_PATH}", 'w', encoding='utf-8') as f:
            json.dump(config_, f, indent=4, ensure_ascii=False)
        return(config_)

def download_videos():
    config_ = get_config()
    if not config_:
        return 0
    agent = bilibili_agent.BilibiliAgent()
    # print(agent.download_video.__doc__)
    bv_or_url = input(F"请输入BV号或者B站视频网页链接(输入q退出):")
    while bv_or_url != 'q':
        agent.download(bv_or_url=bv_or_url, **config_)
        bv_or_url = input(F"请输入BV号或者B站视频网页链接(输入q退出):")

if __name__ == "__main__":
    download_videos()