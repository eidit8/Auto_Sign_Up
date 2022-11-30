import json
import os
import random
from hashlib import md5

import requests

import MessagePush

pwd = os.path.dirname(os.path.abspath(__file__)) + os.sep

headers = {
    "os": "android",
    "phone": "HuaWei|P30|12",
    "appVersion": "39",
    "Sign": "Sign",
    "cl_ip": "192.168.1.2",
    "User-Agent": "okhttp/3.14.9",
    "Content-Type": "application/json;charset=utf-8"
}


def getMd5(text: str):
    return md5(text.encode('utf-8')).hexdigest()


def getDeviceId():
    ret = ""
    for i in range(36):
        num = random.randint(0, 9)
        letter = chr(random.randint(97, 122))  # 取小写字母
        Letter = chr(random.randint(65, 90))  # 取大写字母
        s = str(random.choice([num, letter, Letter]))
        ret += s
    return ret


def parseUserInfo():
    allUser = ''
    if os.path.exists(pwd + "user.json"):
        with open(pwd + "user.json", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                allUser = allUser + line + '\n'
    else:
        return json.loads(os.environ.get("USERS", ""))
    return json.loads(allUser)


def save(user, uid, token):
    url = 'http://sxbaapp.zcj.jyt.henan.gov.cn/interface/clockindaily20220827.ashx'

    data = {
        "dtype": 1,
        "uid": uid,
        "address": user["address"],
        "phonetype": user["deviceType"],
        "probability": -1,
        "longitude": user["longitude"],
        "latitude": user["latitude"]
    }

    headers["Sign"] = getMd5(json.dumps(data) + token)

    res = requests.post(url, headers=headers, data=json.dumps(data))

    if res.json()["code"] == 1001:
        return True, res.json()["msg"]
    return False, res.json()["msg"]


def getToken():
    url = 'http://sxbaapp.zcj.jyt.henan.gov.cn/interface/token.ashx'
    res = requests.post(url, headers=headers)
    return res.json()["data"]["token"]


def login(user, token):
    password = getMd5(user["password"])
    deviceId = user["deviceId"]

    data = {
        "phone": user["phone"],
        "password": password,
        "dtype": 6,
        "dToken": deviceId
    }
    headers["Sign"] = getMd5((json.dumps(data) + token))
    url = 'http://sxbaapp.zcj.jyt.henan.gov.cn/interface/relog.ashx'
    res = requests.post(url, headers=headers, data=json.dumps(data))
    return res.json()


def prepareSign(user):
    if not user["enable"]:
        return

    headers["phone"] = user["deviceType"]

    token = getToken()

    loginResp = login(user, token)

    if loginResp["code"] != 1001:
        print('登录账号失败，错误原因：', loginResp["msg"])
        return

    uid = loginResp["data"]["uid"]
    resp = save(user, uid, token)

    if resp:
        print('打卡成功！')
        return
    print('打卡失败')


if __name__ == '__main__':

    users = parseUserInfo()

    for user in users:
        try:
            prepareSign(user)
        except Exception as e:
            print('职校家园打卡失败，错误原因：' + str(e))
            MessagePush.pushMessage('职校家园打卡失败',
                                    '职校家园打卡失败,' +
                                    '具体错误信息：' + str(e)
                                    , user["pushKey"])
