import requests
import sqlite3
import json
import time
import os



def ele_usage(account):

    session = requests.Session()
    session.cookies.clear()

    url = "https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet"

    data = {
        "param": f'{{"cmd":"h5_getstuindexpage","account":"{account}"}}',
        "customercode": 1575,
    }#这里有一个"roomverify"接口可以指定具体房间号，例如："roomverify":"99-27--175-830"，但是房间号要绑定在学号下

    response = requests.post(
        url, 
        headers={}, 
        data=data,
        proxies=None,
        verify=True  # 验证 SSL 证书
    )

    if response.status_code == 200:
        response_data = response.json()

        if response_data.get("code_") == 0:
            body = json.loads(response_data["body"])
            modist = body.get("modlist", [])
            weekuselist = next(
                (item['weekuselist'] for item in modist if isinstance(item, dict) and 'weekuselist' in item), [])
            room_number = body.get('roomfullname', '房间获取失败')
            current_power = next((item['odd'] for item in modist if isinstance(item, dict) and 'odd' in item), '电量获取失败')
            weekly_usage = []
            for week in weekuselist:
                date = week.get('date', '获取日期失败')
                use = week.get('dayuse', '获取电量失败')
                weekday = week.get('weekday', '星期获取失败')
                weekly_usage.append({"date": date, "usage": use, "day_of_week": weekday})

            return {
                "status_code": 200,
                "room_number": room_number,
                "current_power": current_power,
                "weekly_usage": weekly_usage
            }

        else:
            return {
                "status_code": response_data.get("code_"),
                "error_message": response_data.get("message_")
            }

    else:
        return {
            "status_code": response.status_code,
            "error_message": "请求失败"
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
        




def ele_auto(account):  # 这个函数每隔半小时就会调用一次ele_warning函数检查一次电量，如果电量过低就会返回警告
    while True:
        warning_info = ele_warning(account)
        if warning_info and warning_info["status_code"] == 200 and "warning" in warning_info:
            print({
                "status_code": 200,
                "warning": f"{warning_info['warning']}"
            })

        time.sleep(1800)


#这段函数是用来保存需要使用ele_auto函数用户的学号的，将会保存在account_database.py文件中
def save_user_num():
    # 连接到 SQLite 数据库（如果数据库不存在，会自动创建）
    conn = sqlite3.connect('account_database.db')
    cursor = conn.cursor()

    # 创建表（如果表不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number TEXT UNIQUE NOT NULL,
            wechat_group TEXT NOT NULL
        )
    ''')
    conn.commit()

    print("开始输入学号和对应群组（输入'q'退出）")
    
    while True:
        # 输入学号
        account = input("\n请输入学号：").strip()
        if account.lower() == 'q':
            break
        
        if not account:
            print("学号不能为空，请重新输入")
            continue

        # 输入群组名称
        wechat_group = input("请输入对应的微信群组名称：").strip()
        if wechat_group.lower() == 'q':
            break
        
        if not wechat_group:
            print("群组名称不能为空，请重新输入")
            continue
        
        # 保存学号和群组对应关系
        try:
            cursor.execute('INSERT INTO accounts (student_number, wechat_group) VALUES (?, ?)', (account, wechat_group))
            conn.commit()
            print(f"已添加：学号 {account} -> 提醒微信群： {wechat_group}")
        except sqlite3.IntegrityError:
            print(f"学号 {account} 已存在，请使用其他学号")

    # 查询所有记录
    cursor.execute('SELECT student_number, wechat_group FROM accounts')
    all_accounts = cursor.fetchall()

    # 将结果转换为字典
    existing_accounts = {student_number: wechat_group for student_number, wechat_group in all_accounts}

    # 关闭数据库连接
    conn.close()

    return {
        "status_code": 200,
        "message": "学号和对应微信群组保存成功",
        "accounts": existing_accounts
    }



def load_user_num():
    """从 SQLite 数据库中拉取所有学号和微信群组数据"""
    try:
        # 首先检查数据库文件是否存在
        if not os.path.exists('account_database.db'):
            return {
                "status_code": 500,
                "error_message": "数据库文件 'account_database.db' 不存在"
            }

        # 连接到数据库
        conn = sqlite3.connect('account_database.db')
        cursor = conn.cursor()

        # 查询所有记录
        cursor.execute('SELECT student_number, wechat_group FROM accounts')
        all_accounts = cursor.fetchall()

        # 使用相同的字典推导式格式
        existing_accounts = {student_number: wechat_group for student_number, wechat_group in all_accounts}

        # 关闭数据库连接
        conn.close()

        return {
            "status_code": 200,
            "message": "学号和对应微信群组读取成功",
            "accounts": existing_accounts
        }

    except sqlite3.Error as e:
        return {
            "status_code": 500,
            "error_message": f"数据库操作失败: {str(e)}"
        }
    except Exception as e:
        return {
            "status_code": 500,
            "error_message": f"未知错误: {str(e)}"
        }


#def warning_group: #这段函数是将低电量警告信息发送到指定群组的

