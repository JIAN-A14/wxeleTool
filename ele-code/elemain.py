import re
import plugins
import time
import threading
import time
import logging
from bridge.context import ContextType,Context as EventContext
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf, plugin_config
from .eledef import ele_usage, ele_auto, save_user_num, load_user_num,remove_account_monitoring

@plugins.register(
    name="electricity_plugin",
    desc="A plugin for monitoring electricity usage",
    version="0.1.0",
    author="bingjuu",
    desire_priority=0
)
class ElectricityPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers = {}
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.account_extractor = AccountExtractor()
        self.pending_registrations = {}  # 存储待处理的注册信息
        # 从全局配置获取插件配置
        self.config = self.load_config()
        if not self.config:
            self.config = plugin_config.get("electricity_plugin", {})
        logger.info(f"[电费插件] 初始化完成，配置信息：{self.config}")
        self.start_monitoring()

    def check_query_keywords(self, message):
        """检查是否包含电费查询关键词"""
        return '查' in message and '电费' in message

    def check_monitor_keywords(self, message):
        """检查是否包含电费监控关键词"""
        return '监控' in message and '电费' in message and '取消' not in message

    def check_cancel_keywords(self, message):
        """检查是否包含取消电费监控关键词"""
        return '取消' in message and '电费' in message and '监控' in message

    def send_to_group(self, groupid, reply_text):
        try:
            # 创建上下文对象
            context = EventContext() 
            context.type = ContextType.TEXT
            context.kwargs = {
                "isgroup": True,
                "msg": ChatMessage(
                    groupid=groupid
                )
            }
            
            # 创建事件上下文
            e_context = EventContext()
            e_context["context"] = context
            
            # 创建回复对象
            reply = Reply(ReplyType.TEXT, reply_text)
            e_context["reply"] = reply
            
            # 发送消息
            self.bot.send(e_context, reply)
            logger.info(f"[电费插件] 成功发送消息到群组 {groupid}")
            return True
            
        except Exception as e:
            logger.error(f"[电费插件] 发送消息到群组 {groupid} 失败: {str(e)}")
            return False


    def get_help_text(self, **kwargs):
        help_text = "电费查询与监控插件"
        help_text += "使用说明："
        help_text += "1. 查询电费: 发送包含'电费'和'查'的消息，并附上学号"
        help_text += "2. 监控电费: 发送包含'电费'和'监控'的消息，并附上学号"
        help_text += "3. 取消监控: 发送包含'取消电费监控'的消息，并附上学号"
        return help_text

    def start_monitoring(self):
        logger = logging.getLogger(__name__)
        def monitor_task():
            while True:
                try:
                    # 获取所有注册的账号和群组ID
                    accounts, groupids, result = load_user_num()

                    if result.get("status_code") == 200:
                        # 遍历每个账号和对应的群组ID
                        for account, groupid in zip(accounts, groupids):
                            try:
                                # 检查电费状态
                                warning = ele_auto(account)

                                # 如果有警告信息，则发送到对应的群组
                                if warning and warning.get("status_code") == 200 and warning.get("warning"):
                                    reply = Reply()
                                    reply.type = ReplyType.TEXT
                                    reply.content = warning["warning"]

                                    try:
                                        self.send_to_group(groupid, reply)
                                        logger.info(f"[电费插件] 已发送警告消息到群组 {groupid}")
                                    except Exception as e:
                                        logger.error(f"[电费插件] 发送警告消息到群组 {groupid} 失败：{e}")

                            except Exception as e:
                                logger.error(f"[电费插件] 处理账号 {account} 时出错：{str(e)}")
                                continue

                    else:
                        logger.error(f"[电费插件] 加载用户信息失败: {result.get('message')}")

                except Exception as e:
                    logger.error(f"[电费插件] 监控任务出错：{str(e)}")
                finally:
                    # 从配置中获取检查间隔，默认为10秒
                    check_interval = self.config.get("check_interval", 10)
                    time.sleep(check_interval)

        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        monitor_thread.start()
        logger.info("[电费插件] 监控线程已启动")


    def on_handle_context(self, e_context: EventContext):
        if not self.config.get("enabled", True):
            return

        content = e_context['context'].content
        logger.debug(f"[电费插件] 收到消息：{content}")

        if e_context['context'].type != ContextType.TEXT:
            return

        try:
            reply_content = None


            # 处理电费查询
            if self.check_query_keywords(content):
                        account = self.account_extractor.extract_account(content)
                        if not account:
                            reply_content = "未检测到学号，请发送的消息内容包含'电费'和'查'关键字，并附上学号"
                        else:
                            # 查询电费信息
                            usage_info = ele_usage(account)
                            
                            # 处理查询结果
                            if usage_info.get("status_code") == 200:
                                room_number = usage_info.get("room_number", "未知")
                                current_power = usage_info.get("current_power", "未知")
                                weekly_usage = usage_info.get("weekly_usage", [])
                                
                                # 构建回复内容
                                reply_content = f"宿舍{room_number}当前剩余电量为：{current_power}度\n"
                                reply_content += "最近一周用电情况:\n" + "-" * 30 + "\n"
                                for day in weekly_usage:
                                    reply_content += f"{day['date']} ({day['day_of_week']}): {day['usage']} 度\n"
                            else:
                                reply_content = f"查询失败！错误码: {usage_info['status_code']}, 错误信息: {usage_info.get('error_message', '未知错误')}"
    
            # 发送回复
            if reply_content is not None:
                self._send_reply(e_context, reply_content)

            # 处理电费监控
            if self.check_monitor_keywords(content):
                        account = self.account_extractor.extract_account(content)
                        if not account:
                            reply_content = "未检测到学号，请发送的消息内容包含'电费'和'监控'关键字，并附上学号"
                        else:
                            session_id = e_context['context'].get('session_id')
                            self.pending_registrations[session_id] = account
                            reply_content = "请回复您想要绑定的微信群，该学号的电费提醒将发送到指定微信群"
                        
                        self._send_reply(e_context, reply_content)

            # 处理取消监控
            elif self.check_cancel_keywords(content):
                account = self.account_extractor.extract_account(content)
                if not account:
                    reply_content = "请提供有效的学号"
                else:
                    result = remove_account_monitoring(account)
                    reply_content = result["message"]
                    if result["status_code"] == 200:
                        logger.info(f"[电费插件] 已取消学号 {account} 的监控")
                    elif result["status_code"] == 404:
                        logger.warning(f"[电费插件] 学号 {account} 的监控记录未找到")
            
                self._send_reply(e_context, reply_content)  

            # 处理群组ID回复
            elif e_context['context'].get('session_id') in self.pending_registrations:
                self._handle_group_registration(e_context)

        except Exception as e:
            logger.error(f"[电费插件] 处理消息时发生错误：{str(e)}")
            self._send_reply(e_context, "处理请求时发生错误")

    def _send_reply(self, e_context, content):
        """统一处理回复消息的方法"""
        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = content
        e_context['reply'] = reply
        e_context.action = EventAction.BREAK_PASS

    def _handle_group_registration(self, e_context):
        """处理群组注册的方法"""
        session_id = e_context['context'].get('session_id')
        account = self.pending_registrations[session_id]
        groupid = e_context['context'].get('content').strip()

        if not groupid:
            reply_content = "微信群名不能为空，请重新输入"
        else:
            response = save_user_num(account, groupid)
            del self.pending_registrations[session_id]
            reply_content = response["message"]
            if response["status_code"] == 200:
                logger.info(f"[电费插件] 学号 {account} 已成功绑定到微信群 {groupid}")
        
        self._send_reply(e_context, reply_content)

class AccountExtractor:
    def extract_account(self, text):
        """从消息中提取学号"""
        match = re.search(r'\d{8,20}', text)
        return match.group() if match else None
