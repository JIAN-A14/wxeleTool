import requests
import json
import time


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


#def save_user_num: #这段函数是用来保存需要使用ele_auto函数用户的学号的，将会保存在savenum.py文件中



#def warning_group: #这段函数是将低电量警告信息发送到指定群组的

