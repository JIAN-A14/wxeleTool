import eledef


def test_eleauto(account):
    account = int(input("请输入账户信息: "))
    result = eledef.ele_warning(account)  # 获取ele_warning函数的返回值
    print(result)  # 打印返回的字典信息


if __name__ == "__main__":
    test_eleauto(None)


# def test_eleauto(account):
#     account = int(input("请输入账户信息: "))
#     eledef.ele_auto(account)  # 调用 ele_auto 函数，但不要立即获取返回值

# if __name__ == "__main__":
#     test_eleauto(None)  # 这里传入 None 是因为 test_eleauto 函数会从输入中获取 account 值
