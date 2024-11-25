import requests
import sqlite3
import json
import os
from pathlib import Path



def ele_usage(account):
    try:
        session = requests.Session()
        session.cookies.clear()

        url = "https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet"

        data = {
            "param": f'{{"cmd":"h5_getstuindexpage","account":"{account}"}}',
            "customercode": 1575,
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
                room_number = body.get('roomfullname', '未知房间')

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
                    "current_power": current_power if current_power is not None else '未知电量',
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
                "warning": f"当前电量为: {current_power} 度，电量过低，请注意"
            }
        else:
            return{
                "status_code": 200,
                "warning": f"当前电量为: {current_power} 度，电量正常"
            }#这段else仅用于测试，实际使用时应该删除
    else:
        return{
            "status_code": usage_info["status_code"],
            "error_message": usage_info["error_message"]
        }
        




def ele_auto(account):# 这个函数会调用ele_warning函数检查一次电量，如果电量过低就会返回警告
    """检查电量并返回警告信息"""
    warning_info = ele_warning(account)
    if warning_info and warning_info["status_code"] == 200 and "warning" in warning_info:
        return {
            "status_code": 200,
            "warning": f"{warning_info['warning']}"
        }
    return None



def save_user_num(account, groupid):
    try:
        # 连接到 SQLite 数据库（如果不存在则会创建一个新的）
        db_path = '/root/chatgpt-on-wechat/plugins/findele/accounts.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect('db_path')
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

        # 提交更改
        conn.commit()

        # 关闭连接
        conn.close()

        return {"status_code": 200, "message": "保存成功"}

    except sqlite3.Error as e:
        return {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return {"status_code": 500, "message": f"未知错误: {str(e)}"}



def load_user_num():
    try:
        # 连接到 SQLite 数据库
        db_path = '/root/chatgpt-on-wechat/plugins/findele/accounts.db'
        conn = sqlite3.connect('db_path')
        cursor = conn.cursor()

        # 查询所有记录
        cursor.execute('SELECT account, groupid FROM accounts')
        rows = cursor.fetchall()

        # 关闭连接
        conn.close()

        # 分别提取 account 和 groupid
        accounts = [row[0] for row in rows]
        groupids = [row[1] for row in rows]

        return accounts, groupids, {"status_code": 200, "message": "读取成功"}

    except sqlite3.Error as e:
        return [], [], {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return [], [], {"status_code": 500, "message": f"未知错误: {str(e)}"}




def remove_account_monitoring(account):
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect('db_path')
        cursor = conn.cursor()

        # 检查记录是否存在
        cursor.execute('SELECT * FROM accounts WHERE account = ?', (account,))
        records = cursor.fetchall()

        if not records:
            return {"status_code": 404, "message": "记录未找到"}

        # 删除记录
        cursor.execute('DELETE FROM accounts WHERE account = ?', (account,))
        conn.commit()

        # 关闭连接
        conn.close()

        return {"status_code": 200, "message": "记录删除成功"}

    except sqlite3.Error as e:
        return {"status_code": 500, "message": f"数据库错误: {str(e)}"}

    except Exception as e:
        return {"status_code": 500, "message": f"未知错误: {str(e)}"}
