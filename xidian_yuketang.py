'''
Description: 全自动批量刷课脚本 - 基于抓包JSON数据
'''
import os
import json
import time
import requests
import asyncio
import webbrowser
import websockets

session = requests.Session()

csrftoken = None
sessionid = None
django_language = None
login_type = None


def login_sync():
    asyncio.run(login())

    if not sessionid:
        raise RuntimeError("扫码登录失败，没有获取到 sessionid")

    return {
        "csrftoken": csrftoken,
        "sessionid": sessionid,
        "django_language": django_language,
        "login_type": login_type,
    }


async def login():
    uri = "wss://www.yuketang.cn/wsapp"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.yuketang.cn",
    }

    payload = {
        "op": "requestlogin",
        "role": "web",
        "version": 1.4,
        "type": "qrcode",
        "from": "web",
    }

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        await websocket.send(json.dumps(payload))

        while True:
            message = await websocket.recv()

            if "ticket" in message:
                handle_qrcode(message)

            if "subscribe_status" in message:
                handle_login_success(message)
                extract_cookies()
                break


def handle_qrcode(message):
    data = json.loads(message)
    qrcode_url = data["ticket"]

    response = session.get(qrcode_url)
    response.raise_for_status()

    qrcode_path = os.path.abspath("qrcode.png")

    with open(qrcode_path, "wb") as f:
        f.write(response.content)

    print("请扫码登录...")
    webbrowser.open("file://" + qrcode_path)


def handle_login_success(message):
    data = json.loads(message)

    auth = data["Auth"]
    user_id = data["UserID"]

    login_url = "https://www.yuketang.cn/pc/web_login"

    payload = json.dumps({
        "UserID": user_id,
        "Auth": auth,
    })

    response = session.post(login_url, data=payload)
    response.raise_for_status()


def extract_cookies():
    global csrftoken, sessionid, django_language, login_type

    csrftoken = session.cookies.get("csrftoken")
    sessionid = session.cookies.get("sessionid")
    django_language = session.cookies.get("django_language")
    login_type = session.cookies.get("login_type")


def get_cookie_string():
    return (
        f"csrftoken={csrftoken}; "
        f"sessionid={sessionid}; "
        f"django_language={django_language}; "
        f"login_type={login_type}"
    )


# ================= 配置区域 =================
cookie_info = login_sync()

COOKIE = cookie_info["sessionid"]
CSRFTOKEN = cookie_info["csrftoken"]
DJANGO_LANGUAGE = cookie_info["django_language"]
LOGIN_TYPE = cookie_info["login_type"]

print(COOKIE)
print(CSRFTOKEN)
print(DJANGO_LANGUAGE)
print(LOGIN_TYPE)
# 1. 在这里填入你的 Cookie (sessionid)
# COOKIE = 'x5e5i579nujrvr1itij92pild7tmsrtw'




url = "https://www.yuketang.cn/v2/api/web/courses/list?identity=2"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.yuketang.cn/v2/web/index",
    "Cookie": f"sessionid={COOKIE}; csrftoken={CSRFTOKEN}; django_language={DJANGO_LANGUAGE}"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise RuntimeError("获取课程列表失败")

data_obj = response.json()   # ⭐ 直接替代 json.loads
course_list = data_obj['data']['list']

print(f"成功加载课程列表，共发现 {len(course_list)} 门课程")

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from typing import List
from time import sleep
import random

IF_HEADLESS = False

# 配置浏览器
option = webdriver.ChromeOptions()
option.add_argument('--no-proxy-server')
option.add_argument("--disable-blink-features=AutomationControlled")
if IF_HEADLESS:
    option.add_argument('--headless')

print("正在启动浏览器...")
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
except Exception as e:
    print(f"浏览器启动失败: {e}")
    exit()

driver.maximize_window()
driver.implicitly_wait(10)
IS_COMMONUI = False


# ----------------- 辅助函数 -----------------
def set_playback_speed(speed=2.0):
    """
    使用JS强制修改播放倍速
    :param speed: 倍速数值 (建议不要超过2.0，否则可能不记录进度)
    """
    try:
        # 直接修改 video 标签的 playbackRate 属性
        driver.execute_script(f'document.querySelector("video").playbackRate = {speed};')
        print(f"  >> [JS] 已开启 {speed} 倍速播放")
    except Exception as e:
        print(f"  >> 倍速设置失败: {e}")
def setCookie(cookies):
    driver.delete_all_cookies()
    for name, value in cookies.items():
        driver.add_cookie({'name': name, 'value': value, 'path': '/'})


def ifVideo(div: WebElement):
    for i in div.find_elements(By.TAG_NAME, 'i'):
        if 'icon--suo' in i.get_attribute('class'): return False  # 锁住的

    if IS_COMMONUI:
        try:
            span = div.find_element(By.CSS_SELECTOR, 'span.leaf-flag')
            return '视频' in span.text.strip()
        except:
            return False

    try:
        i = div.find_element(By.TAG_NAME, 'i')
        return 'icon--shipin' in i.get_attribute('class')
    except:
        return False


def getAllvideos_notFinished(allClasses: List[WebElement]):
    driver.implicitly_wait(0.1)
    allVideos = []
    for thisClass in allClasses:
        # 核心逻辑：是视频 且 文本里没有“已完成”
        if ifVideo(thisClass) and '已完成' not in thisClass.text:
            print(f'  >> 发现未完成: {thisClass.text.strip()}')
            allVideos.append(thisClass)
    driver.implicitly_wait(10)
    return allVideos


def change2speed2():
    try:
        speedbutton = driver.find_element(By.TAG_NAME, 'xt-speedbutton')
        ActionChains(driver).move_to_element(speedbutton).perform()
        ul = speedbutton.find_element(By.TAG_NAME, 'ul')
        lis = ul.find_elements(By.TAG_NAME, 'li')
        li_speed2 = lis[0]
        diffY = speedbutton.location['y'] - li_speed2.location['y']
        for i in range(diffY // 10):
            ActionChains(driver).move_by_offset(0, -10).perform()
            sleep(0.5)
        sleep(0.8)
        ActionChains(driver).click().perform()
    except:
        pass


def mute1video():
    try:
        if not driver.execute_script('return video.muted;'):
            voice = driver.find_element(By.TAG_NAME, 'xt-volumebutton')
            ActionChains(driver).move_to_element(voice).perform()
            ActionChains(driver).click().perform()
    except:
        pass


# def finish1video():
#     """刷一个视频的逻辑"""
#     global IS_COMMONUI
#     if IS_COMMONUI:
#         try:
#             driver.find_element(By.ID, 'tab-student_school_report').click()
#             sleep(1)
#             allClasses = driver.find_elements(By.CLASS_NAME, 'study-unit')
#         except:
#             allClasses = []
#     else:
#         allClasses = driver.find_elements(By.CLASS_NAME, 'leaf-detail')
#
#     allVideos = getAllvideos_notFinished(allClasses)
#     if not allVideos:
#         return False  # 当前页面没有未完成的视频了
#
#     video_element = allVideos[0]
#     driver.execute_script('arguments[0].scrollIntoView(false);', video_element)
#
#     if IS_COMMONUI:
#         video_element.find_element(By.TAG_NAME, 'span').click()
#     else:
#         video_element.click()
#
#     print('  >> 正在播放...')
#     driver.switch_to.window(driver.window_handles[-1])
#
#     try:
#         WebDriverWait(driver, 15).until(
#             lambda x: driver.execute_script('video = document.querySelector("video"); return video;'))
#     except:
#         print("  >> 视频加载超时或非视频页面，关闭重试")
#         driver.close()
#         driver.switch_to.window(driver.window_handles[0])
#         return True  # 返回True以便重试下一轮
#
#     # 注入播放脚本
#     driver.execute_script('videoPlay = setInterval(function() {if (video.paused) {video.play();}}, 200);')
#     driver.execute_script('setTimeout(() => clearInterval(videoPlay), 5000)')
#     driver.execute_script(
#         'addFinishMark = function() {finished = document.createElement("span"); finished.setAttribute("id", "LetMeFly_Finished"); document.body.appendChild(finished);}')
#     driver.execute_script(
#         'lastDuration = 0; setInterval(() => {nowDuration = video.currentTime; if (nowDuration < lastDuration) {addFinishMark()}; lastDuration = nowDuration}, 200)')
#     driver.execute_script('video.addEventListener("pause", () => {video.play()})')
#
#     mute1video()
#     change2speed2()
#
#     # 循环等待播放完成
#     wait_count = 0
#     while True:
#         if driver.execute_script('return document.querySelector("#LetMeFly_Finished");'):
#             print('  >> 视频已播放完毕')
#             sleep(3)
#             driver.close()
#             driver.switch_to.window(driver.window_handles[0])  # 切回课程主页
#             return True
#         else:
#             if wait_count % 10 == 0:
#                 print(f'  >> 正在播放中... {random.random():.2f}')
#             sleep(3)
#             wait_count += 1
#     return False


# ================= 主程序逻辑 =================

# 1. 解析JSON获取课程列表
def finish1video():
    """刷一个视频的逻辑"""
    global IS_COMMONUI
    if IS_COMMONUI:
        try:
            driver.find_element(By.ID, 'tab-student_school_report').click()
            sleep(1)
            allClasses = driver.find_elements(By.CLASS_NAME, 'study-unit')
        except:
            allClasses = []
    else:
        allClasses = driver.find_elements(By.CLASS_NAME, 'leaf-detail')

    allVideos = getAllvideos_notFinished(allClasses)
    if not allVideos:
        return False  # 当前页面没有未完成的视频了

    video_element = allVideos[0]
    driver.execute_script('arguments[0].scrollIntoView(false);', video_element)
    # driver.execute_script('video.addEventListener("pause", () => {video.play()})')
    #
    # mute1video()
    # set_playback_speed(2.0)  # <--- 改成这个，括号里填你想几倍速
    if IS_COMMONUI:
        video_element.find_element(By.TAG_NAME, 'span').click()
    else:
        video_element.click()

    print('  >> 正在播放...')
    driver.switch_to.window(driver.window_handles[-1])

    try:
        WebDriverWait(driver, 15).until(
            lambda x: driver.execute_script('video = document.querySelector("video"); return video;'))
    except:
        print("  >> 视频加载超时或非视频页面，关闭重试")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return True  # 返回True以便重试下一轮

    # 注入播放脚本
    driver.execute_script('videoPlay = setInterval(function() {if (video.paused) {video.play();}}, 200);')
    driver.execute_script('setTimeout(() => clearInterval(videoPlay), 5000)')
    driver.execute_script(
        'addFinishMark = function() {finished = document.createElement("span"); finished.setAttribute("id", "LetMeFly_Finished"); document.body.appendChild(finished);}')
    driver.execute_script(
        'lastDuration = 0; setInterval(() => {nowDuration = video.currentTime; if (nowDuration < lastDuration) {addFinishMark()}; lastDuration = nowDuration}, 200)')
    driver.execute_script('video.addEventListener("pause", () => {video.play()})')

    mute1video()
    change2speed2()

    # 循环等待播放完成
    wait_count = 0
    while True:
        if driver.execute_script('return document.querySelector("#LetMeFly_Finished");'):
            print('  >> 视频已播放完毕')
            sleep(3)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])  # 切回课程主页
            return True
        else:
            if wait_count % 10 == 0:
                print(f'  >> 正在播放中... {random.random():.2f}')
            sleep(3)
            wait_count += 1
    return False
try:
    data_obj = response.json()
    course_list = data_obj['data']['list']
    print(f"成功加载课程列表，共发现 {len(course_list)} 门课程")
except Exception as e:
    print(f"JSON解析失败，请检查格式: {e}")
    exit()

# 2. 遍历每一门课
for index, course in enumerate(course_list):
    course_name = course['name']
    classroom_id = course['classroom_id']
    university_id = course['course']['university_id']

    # 构建当前课程的URL
    current_course_url = f'https://www.yuketang.cn/v2/web/studentLog/{classroom_id}?university_id={university_id}&platform_id=3&classroom_id={classroom_id}&content_url='

    print(f"\n[{index + 1}/{len(course_list)}] 正在处理课程: {course_name}")
    print(f"地址: {current_course_url}")

    # 访问课程主页
    homePageURL = 'https://www.yuketang.cn/'  # 默认通用首页
    driver.get(homePageURL)
    setCookie({'sessionid': COOKIE})  # 每次都确保Cookie有效
    driver.get(current_course_url)
    sleep(3)

    # 登录检查
    if 'pro/portal/home' in driver.current_url or 'login' in driver.current_url:
        print('Cookie可能失效，尝试自动跳转登录页...')
        driver.get('https://www.yuketang.cn/web?next=' + current_course_url)
        print(">>> 请在浏览器中扫码登录，登录成功后脚本会自动继续 <<<")
        while 'studentLog' not in driver.current_url:
            sleep(1)
        print('登录成功！')

    # 界面类型判断
    IS_COMMONUI = 'www.yuketang.cn' in driver.current_url

    # 3. 循环刷该课程的所有视频
    print(f"开始扫描 {course_name} 的未完成视频...")
    while finish1video():
        print("刷新课程主页状态...")
        driver.refresh()
        sleep(5)

    print(f"√ 课程 [{course_name}] 所有视频处理完毕 (或无未完成视频)")
    sleep(2)

print('\n==================================')
print('恭喜你！所有列表中的课程都已巡检完毕！')
print('==================================')
driver.quit()