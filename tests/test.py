import requests
import os
import re
import json

headers = {}
# headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
headers["referer"] = "https://www.bilibili.com/"

# <video crossorigin="anonymous" preload="auto" src="blob:https://www.bilibili.com/d4dac259-bb4c-43ed-a844-e9b8920ca3a1"></video>
if __name__ == "__main__":
    url ="https://www.bilibili.com/bangumi/play/ss44151?from_spmid=666.4.hotlist.0"
    url ="https://www.bilibili.com/bangumi/play/ep743053?from_spmid=666.4.schedule.2"
    headers["referer"] = url
    web_res = requests.get(url, headers=headers)
    dec = web_res.content.decode('utf-8')
    with open(F"tests/test.html", 'w', encoding='utf-8') as f:
        f.write(dec)
    with open(F"tests/test2.html", 'w', encoding='utf-8') as f:
        f.write(web_res.text)
    re_INITIAL_STATE = 'window.__INITIAL_STATE__=([\s\S]*?);\(function'
    INITIAL_STATE = re.findall(re_INITIAL_STATE, dec, re.S)
    # print(INITIAL_STATE)
    temp = json.loads(INITIAL_STATE[0])
    with open(F"tests/test.json", 'w', encoding='utf-8') as f:
        json.dump(temp, f, ensure_ascii=False)