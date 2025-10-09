import asyncio
import time
import requests
import websockets
import json
import webbrowser
import os

import time
import sys
import pickle

session = requests.Session()


# 保存cookie到文件
def save_cookies(session, filename):
    with open(filename, 'wb') as file:
        pickle.dump(session.cookies, file)

# 从文件加载cookie
def load_cookies(session, filename):
    with open(filename, 'rb') as file:
        session.cookies.update(pickle.load(file))

async def websocket_session():
    uri = "wss://www.yuketang.cn/wsapp"  # WebSocket 服务器的 URI
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36',
        'Origin': "https://www.yuketang.cn",
    }
    data = {
        "op": "requestlogin",
        "role": "web",
        "version": 1.4,
        "type": "qrcode",
        "from": "web"
    }
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # 将字典转换为JSON字符串并发送
        json_data = json.dumps(data)
        await websocket.send(json_data)
        # 保持连接并监听服务器的消息
        while True:
                response = await websocket.recv()
                if 'ticket' in response:
                    response_json = json.loads(response)
                    url = response_json['ticket']
                    response = session.get(url=url)
                    # 使用默认的图像查看器打开图像
                    if response.status_code == 200:
                        # 保存图片
                        with open('sunci.png', 'wb') as file:
                            file.write(response.content)
                        # 打开图片
                        print("大人请微信扫码！！")
                        webbrowser.open('file://' + os.path.realpath('sunci.png'))
                    else:
                        print(f"Failed to retrieve the image. Status code: {response.status_code}")
                if 'subscribe_status' in response:
                    json_data = json.loads(response)
                    auth = json_data['Auth']
                    UserID = json_data['UserID']
                    url = "https://www.yuketang.cn/pc/web_login"
                    data = '{"UserID":'+str(UserID)+',"Auth":"'+auth+'"}'
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
                    response = session.post(url,data,headers)

                    # 保存cookie
                    save_cookies(session, 'cookies.pkl')

                    break

        ssxx()
# 彩色输出辅助函数
def color_text(text, color="green"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def progress_bar(percent, length=30):
    filled = int(length * percent / 100)
    bar = '█' * filled + '-' * (length - filled)
    return f"[{bar}] {percent:>3}%"

def ssxx():
    url = 'https://www.yuketang.cn/v2/api/web/courses/list?identity=2'
    response = session.get(url=url)
    JSON = json.loads(response.text)

    if len(JSON['data']['list']) > 1:
        print(color_text("📚 当前已选课程列表：", "cyan"))
        for i, c in enumerate(JSON['data']['list']):
            print(color_text(f"  {i}. {c['name']}", "yellow"))

        min_value = 0
        max_value = len(JSON['data']['list']) - 1

        while True:
            user_input = input(color_text("\n请输入要观看的课程序号（可输入多个，用空格或逗号分隔）：\n", "green"))
            parts = [x.strip() for x in user_input.replace('，', ',').replace(' ', ',').split(',') if x.strip()]
            try:
                nums = [int(x) for x in parts]
                if all(min_value <= n <= max_value for n in nums):
                    break
                else:
                    print(color_text(f"❌ 输入错误：编号应在 {min_value}~{max_value} 范围内", "red"))
            except ValueError:
                print(color_text("❌ 输入无效，请输入整数，用空格或逗号分隔。", "red"))

        # 循环处理多个课程
        for num in nums:
            global classroom_id
            classroom_id = str(JSON['data']['list'][num]['classroom_id'])
            course_name = JSON['data']['list'][num]['name']
            print(color_text(f"\n🎬 正在进入课程：《{course_name}》", "blue"))

            url = f"https://www.yuketang.cn/v2/api/web/logs/learn/{classroom_id}?actype=-1&page=0&offset=20&sort=-1"
            response = session.get(url)
            JSON_detail = json.loads(response.text)

            # 获取课程详情
            url = 'https://www.yuketang.cn/c27/online_courseware/xty/kls/pub_news/' + str(
                JSON_detail['data']['activities'][1]['courseware_id']) + '/'
            headers = {'xtbz': 'ykt', 'classroom-id': str(classroom_id)}
            response = session.get(url, headers=headers)
            JSON_course = json.loads(response.text)
            c_course_id = str(JSON_course['data']['course_id'])
            s_id = str(JSON_course['data']['s_id'])

            for i, chapter in enumerate(JSON_course['data']['content_info']):
                print(color_text(f"\n📖 正在学习章节 {i+1}：{chapter['name']}（共 {len(chapter['section_list'])} 个视频）", "cyan"))

                for j, section in enumerate(chapter['section_list']):
                    video_id = str(section['leaf_list'][0]['id'])
                    url = f'https://www.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/{classroom_id}/{video_id}/'
                    response = session.get(url=url, headers=headers)
                    JSON_TEMP = json.loads(response.text)
                    ccid = JSON_TEMP['data']['content_info']['media']['ccid']
                    d = JSON_TEMP['data']['content_info']['media']['duration']
                    v = str(JSON_TEMP['data']['id'])
                    u = str(JSON_TEMP['data']['user_id'])
                    timestamp_ms = int(time.time() * 1000)

                    url_progress = f"https://www.yuketang.cn/video-log/get_video_watch_progress/?cid={c_course_id}&user_id={u}&classroom_id={classroom_id}&video_type=video&vtype=rate&video_id={video_id}&snapshot=1"
                    response_new = session.get(url=url_progress, headers=headers)
                    JSON_NEW = json.loads(response_new.text)

                    try:
                        sunci = JSON_NEW['data'][video_id]['completed']
                    except:
                        sunci = 0

                    if sunci == 1:
                        print(color_text(f"✅ 视频 {j+1} 已观看，自动跳过。", "yellow"))
                        continue

                    print(color_text(f"▶️ 正在观看第 {i+1} 章 - 第 {j+1} 个视频", "green"))

                    # 模拟进度条播放
                    for k in range(25):
                        time.sleep(0.6)
                        sys.stdout.write('\r' + progress_bar(4 * (k + 1)))
                        sys.stdout.flush()
                    print()  # 换行

                    print(color_text(f"✔️ 视频 {j+1} 已完成！", "green"))

            print(color_text(f"\n🎉 课程《{course_name}》已观看完成！\n", "cyan"))

        print(color_text("✅ 所有选中的课程均已观看完毕！", "green"))
    else:
        print(color_text("❌ 你没有选课！", "red"))
        exit(-1)



if __name__ == "__main__":
    print("Start:")
    # 在程序启动时，尝试加载cookie
    try:
        load_cookies(session, 'cookies.pkl')
        # 测试cookie是否有效，比如访问一个需要登录的页面
        response = session.get('https://www.yuketang.cn/v2/api/web/courses/list?identity=2')
        if response.status_code != 200 or 'login' in response.url:
            raise Exception("Cookies are invalid or expired")
        else:
            ssxx()
    except Exception as e:
        print("Cookies are invalid or expired, need to login again")
        asyncio.run(websocket_session())
        # exit()



# 运行异步函数
asyncio.run(websocket_session())
    # # 运行异步函数
    # asyncio.run(websocket_session())
