import eledef
import json


# 示例调用
# if __name__ == "__main__":
#     result = eledef.save_user_num()
#     print(result)



def test_load_user_num():
    """测试从数据库加载数据并打印所有记录"""
    result = eledef.load_user_num()
    
    if result["status_code"] == 200:
        accounts = result["accounts"]
        print("\n数据库中的所有记录：")
        print("-" * 40)
        print("学号\t\t微信群组")
        print("-" * 40)
        for student_number, wechat_group in accounts.items():
            print(f"{student_number}\t{wechat_group}")
        print("-" * 40)
        print(f"总记录数: {len(accounts)}")
    else:
        print(f"错误: {result['error_message']}")

# 执行测试
if __name__ == "__main__":
    test_load_user_num()



# eledef.save_user_num()

# result = eledef.ele_warning(account)  # 获取ele_warning函数的返回值
# print(result)  # 打印返回的字典信息



# save_user_num()
# test_eleauto(None)


# def test_eleauto(account):
#     account = int(input("请输入账户信息: "))
#     eledef.ele_auto(account)  # 调用 ele_auto 函数，但不要立即获取返回值

# if __name__ == "__main__":
#     test_eleauto(None)  # 这里传入 None 是因为 test_eleauto 函数会从输入中获取 account 值
