import requests
import json
import os

def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config.json')
    template_path = os.path.join(current_dir, 'config.json.template')
    if not os.path.exists(config_path):
        config_path = template_path

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r',encoding='utf-8') as f:
                config = json.load(f)
                return config


    except json.JSONDecodeError:
        return {"warning": "配置文件解析错误，将使用默认配置"}
    except Exception as e:
        return {"warning": f"读取配置文件失败: {str(e)}"}

def ele_usage(account):
    try:
        customercode = load_config().get("customercode")
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
    
def test_ele_usage():
    try:
        # 获取用户输入
        print("欢迎使用电量查询系统")
        print("-" * 30)
        account = input("请输入您的账号: ")
        
        # 调用函数并获取结果
        print("正在查询，请稍候...")
        result = ele_usage(account)
        
        # 处理返回结果
        if result["status_code"] == 200:
            print("查询成功！")
            print(f"房间号: {result['room_number']}")
            print(f"当前电量: {result['current_power']}")
            
            print("最近一周用电情况:")
            print("-" * 30)
            for day in result["weekly_usage"]:
                print(f"{day['date']} ({day['day_of_week']}): {day['usage']} 度")
        else:
            print("\n查询失败！")
            print(f"错误码: {result['status_code']}")
            print(f"错误信息: {result['error_message']}")
            
    except requests.exceptions.ConnectionError:
        print("连接服务器失败，请检查网络连接！")
    except json.JSONDecodeError:
        print("\n解析服务器返回数据失败！")
    except Exception as e:
        print(f"发生未知错误：{str(e)}")
    
    print("\n" + "-" * 30)

if __name__ == "__main__":
    test_ele_usage()

