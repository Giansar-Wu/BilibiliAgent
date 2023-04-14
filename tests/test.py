import requests
import os

headers = {}
# headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
headers["referer"] = "https://www.bilibili.com/"

def test():
    return 1,2,3

if __name__ == "__main__":
    # url ="https://passport.bilibili.com/qrcode/getLoginUrl"
    # headers["referer"] = url
    # web_res = requests.get(url=url, headers=headers)
    # with open(F"test.html", 'w', encoding='utf-8') as f:
    #     f.write(web_res.text)
    x = test()
    print(x)