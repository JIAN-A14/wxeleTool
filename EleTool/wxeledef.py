import requests
import sqlite3
import json
import os
from pathlib import Path
from bridge.reply import Reply, ReplyType
from channel.wechat.wechat_channel import WechatChannel
from common.log import logger
from lib import itchat
import io
import requests



def ele_usage(account,customercode):
    try:
        session = requests.Session()
        session.cookies.clear()

        url = "https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet"

        data = {
            "param": f'{{"cmd":"h5_getstuindexpage","account":"{account}"}}',
            "customercode": {customercode},
        }

        # 发送请求
        response = requests.post(
            url, 
            headers={}, 
            data=data,
            proxies=None,
            verify=True
        )

        # 打印原始响应数据，用于调试
        print(f"Raw Response: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            
            # 打印解析后的响应数据
            print(f"Parsed Response: {response_data}")

            if response_data.get("code_") == 0:
                body = json.loads(response_data["body"])
                
                # 打印body数据
                print(f"Body Data: {body}")

                # 获取房间号
                room_number = body.get('roomfullname', [])

                # 获取电费信息
                modist = body.get("modlist", [])
                current_power = None
                weekuselist = None

                # 遍历modlist查找电费和用电记录
                for item in modist:
                    if not isinstance(item, dict):
                        continue
                    
                    # 获取当前电费
                    if 'odd' in item:
                        current_power = item['odd']
                    
                    # 获取周用电记录
                    if 'weekuselist' in item:
                        weekuselist = item['weekuselist']

                # 处理周用电数据
                weekly_usage = []
                if weekuselist:
                    for week in weekuselist:
                        if isinstance(week, dict):
                            usage_entry = {
                                "date": week.get('date', '未知日期'),
                                "usage": week.get('dayuse', '0'),
                                "day_of_week": week.get('weekday', '未知')
                            }
                            weekly_usage.append(usage_entry)

                # 构建返回数据
                return {
                    "status_code": 200,
                    "room_number": room_number,
                    "current_power": current_power if current_power is not None else '该学号未绑定房间号',
                    "weekly_usage": weekly_usage
                }
            else:
                # API 返回错误
                return {
                    "status_code": response_data.get("code_"),
                    "error_message": response_data.get("message_", "未知错误")
                }
        else:
            # HTTP 请求失败
            return {
                "status_code": response.status_code,
                "error_message": "HTTP请求失败"
            }

    except json.JSONDecodeError as e:
        # JSON 解析错误
        print(f"JSON解析错误: {str(e)}")
        return {
            "status_code": 500,
            "error_message": "数据格式错误"
        }
    except Exception as e:
        # 其他异常
        print(f"发生错误: {str(e)}")
        return {
            "status_code": 500,
            "error_message": f"系统错误: {str(e)}"
        }



def ele_warning(account):#这段函数会调用ele_usage函数，如果电量过低就会返回警告
    usage_info = ele_usage(account)

    if usage_info["status_code"] == 200:
        current_power = usage_info["current_power"]
        room_number = usage_info["room_number"]
        
        if current_power is not None and isinstance(current_power,(int,float)) and current_power < 20:
            return {
                "status_code": 200,
                "warning": f"当前电量为: {current_power} 度，电量过低，尽快充电费捏"
            }
        else:
            return{
                "status_code": 200,
                "warning": f"当前电量为: {current_power} 度，电量正常"
            }#这段else不需要可以删除
    else:
        return{
            "status_code": usage_info["status_code"],
            "error_message": usage_info["error_message"]
        }
        




def ele_auto(account):# 这个函数会调用ele_warning函数检查一次电量，这个中间商函数是前期构思拉出来的，最后为这个函数设想的功能集成在elemain里了，为了让它有点作用就把他放着了
    """检查电量并返回警告信息"""
    warning_info = ele_warning(account)
    if warning_info and warning_info["status_code"] == 200 and "warning" in warning_info:
        return {
            "status_code": 200,
            "warning": f"{warning_info['warning']}"
        }
    return None



def save_user_num(account, groupid):#可以自行修改数据库保存的地址
    # 连接到 SQLite 数据库（如果不存在则会创建一个新的）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'accounts.db')

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

        # 创建表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    groupid TEXT NOT NULL
                )
            ''')

            # 插入新的记录
            cursor.execute('''
                INSERT INTO accounts (account, groupid) VALUES (?, ?)
            ''', (account, groupid))


            return {"status_code": 200, "message": "保存成功"}

    except sqlite3.Error as e:
        return {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return {"status_code": 500, "message": f"未知错误: {str(e)}"}



def load_user_num():
    # 连接到 SQLite 数据库
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'accounts.db')
        
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute('SELECT account, groupid FROM accounts')
            rows = cursor.fetchall()


            # 分别提取 account 和 groupid
            accounts = [row[0] for row in rows]
            groupids = [row[1] for row in rows]

            return accounts, groupids, {"status_code": 200, "message": "读取成功"}

    except sqlite3.Error as e:
        return [], [], {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return [], [], {"status_code": 500, "message": f"未知错误: {str(e)}"}




def remove_account_monitoring(account):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'accounts.db')

    try:
        with sqlite3.connect(db_path) as conn:
            # 连接到 SQLite 数据库
            cursor = conn.cursor()

            # 检查记录是否存在
            cursor.execute('SELECT * FROM accounts WHERE account = ?', (account,))
            records = cursor.fetchall()

            if not records:
                return {"status_code": 404, "message": "记录未找到"}

            # 删除记录
            cursor.execute('DELETE FROM accounts WHERE account = ?', (account,))


            return {"status_code": 200, "message": "记录删除成功"}

    except sqlite3.Error as e:
        return {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return {"status_code": 500, "message": f"未知错误: {str(e)}"}


def check_login():#检查微信是否成功登录
    try:
        # 检查 itchat 实例是否存在
        if not hasattr(itchat, 'instance'):
            return False
        
        # 检查 storage 是否初始化
        if not hasattr(itchat.instance, 'storageClass'):
            return False
        
        # 检查是否有有效的用户名
        if not itchat.instance.storageClass.userName:
            return False
            
        # 检查是否在线
        if not itchat.instance.alive:
            return False
        
        # 检查登录状态
        if itchat.instance.loginInfo.get('wxuin') is None:
            return False
            
        return True
    
    except Exception as e:
        return False


def send_to_group(group_name: str, message, msg_type: str = 'text'):
    """
    发送消息到指定群组
    :param group_name: 群组名称
    :param message: 要发送的消息内容
    :param msg_type: 消息类型，支持 'text', 'image', 'file', 'voice', 'video'
    :return: bool 发送成功返回False
    """
    try:
        # 获取WechatChannel实例
        wx_channel = WechatChannel()
        
        # 查找群组
        group = itchat.search_chatrooms(name=group_name)
        if not group:
            logger.error(f"[WX] Group '{group_name}' not found")
            return False
            
        group_id = group[0]['UserName']
        
        # 构造Reply对象
        reply = Reply()
        
        # 根据消息类型设置Reply
        if msg_type.lower() == 'text':
            reply.type = ReplyType.TEXT
            reply.content = message
            
        elif msg_type.lower() == 'image':
            if isinstance(message, str):  # 如果是URL
                if message.startswith(('http://', 'https://')):
                    reply.type = ReplyType.IMAGE_URL
                    reply.content = message
                else:  # 如果是本地文件路径
                    reply.type = ReplyType.IMAGE
                    with open(message, 'rb') as f:
                        reply.content = io.BytesIO(f.read())
            else:  # 如果是二进制数据
                reply.type = ReplyType.IMAGE
                reply.content = io.BytesIO(message)
                
        elif msg_type.lower() == 'file':
            reply.type = ReplyType.FILE
            reply.content = message
            
        elif msg_type.lower() == 'voice':
            reply.type = ReplyType.VOICE
            reply.content = message
            
        elif msg_type.lower() == 'video':
            if isinstance(message, str) and message.startswith(('http://', 'https://')):
                reply.type = ReplyType.VIDEO_URL
                reply.content = message
            else:
                reply.type = ReplyType.VIDEO
                reply.content = message
        else:
            logger.error(f"[WX] Unsupported message type: {msg_type}")
            return False
            
        # 构造Context
        context = {
            "receiver": group_id,
            "isgroup": True
        }
        
        # 发送消息
        wx_channel.send(reply, context)
        logger.info(f"[WX] Message sent to group {group_name} successfully")
        return True
        
    except Exception as e:
        logger.error(f"[WX] Error sending message to group {group_name}: {str(e)}")
        return False
# 使用例
"""
# 发送文本
send_to_group("让我测测", "Hello World", "text")
# 发送图片URL
send_to_group("让我测测", "https://img.smnet1.com/files.php?filename=1732586034-22163899.png", "image")
# 发送本地图片
send_to_group("让我测测", "我去我喜欢铃兰.jpg", "image")
# 发送文件
send_to_group("让我测测", "114514.zip", "file")
# 发送视频
send_to_group("让我测测", "野兽先辈.mp4", "video")
"""
