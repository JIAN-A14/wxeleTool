import requests
import json
from EleTool.wxeledef import ele_usage

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

