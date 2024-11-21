# encoding:utf-8

import re
import requests
import json

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf
from .eledef import ele_usage

@plugins.register(
    name="findele",
    desire_priority=1,
    hidden=True,
    desc="findele",
    version="0.2",
    author="bingjuu",
)


class ElectricityPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

    
        content = e_context['context'].content

        if "查" in content and "电费" in content:
            account = self.extract_account_number(content)  # 提取账户信息
            if account is None:
                reply_content = "你好像没有告诉我你的学号捏，你应该告诉我：要查询（你的学号）的电费"
            else:
                try:
                    output = ele_usage(account)  # 直接调用函数

                    if output.get("status_code") == 200:
                        current_power = output.get("current_power")
                        room_number = output.get("room_number")

                        if current_power is not None:
                            reply_content = f"房间{room_number}当前电量为: {current_power} 度"
                        else:
                            reply_content = "获取电量失败。"
                    else:
                        reply_content = f"获取电费信息时出错，错误代码: {output.get('status_code')}, 消息: {output.get('error_message')}"

                    reply = Reply()
                    reply.type = ReplyType.TEXT  # 设置回复类型为文本
                    reply.content = reply_content  # 将输出内容设置为回复内容
                    e_context['reply'] = reply  # 将回复对象添加到上下文中
                    e_context.action = EventAction.BREAK_PASS

                except Exception as e:
                    logger.error(f"[findele] 获取电费信息时出错：{e}")
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = "获取电费信息时出错，请稍后再试。"
                    e_context['reply'] = reply  # 将错误回复对象添加到上下文中
                    e_context.action = EventAction.BREAK_PASS



    def extract_account_number(self, message):
        try:
            # 使用正则表达式匹配8-12位数字（根据你的学号实际长度调整）
            pattern = r'\d{8,16}'
            match = re.search(pattern, message)
            if match:
                return int(match.group())
            return None
        except:
            return None

