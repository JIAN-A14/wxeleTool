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
from .elemain import ele_usage

@plugins.register(
    name="findele",
    desire_priority=1,
    hidden=True,
    desc="findele",
    version="0.1",
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

        if content == "查电费":
            account = "20225080905085"  # 未来可以自行输入
            try:
                output = ele_usage(account)  # 直接调用函数

                if output.get("status_code") == 200:
                    current_power = output.get("current_power")

                    if current_power is not None:
                        reply_content = f"当前电量为: {current_power} 度"
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
