import plugins
from bridge.context import ContextType, EventContext, EventAction
from bridge.reply import Reply, ReplyType
from plugins import *
from config import plugin_config
from common.log import logger
import threading
import time
import re
from .eledef import ele_usage, ele_auto, save_user_num, load_user_num, remove_account_monitoring

@plugins.register(
    name="electricity_plugin",
    desc="一个用于监控电费的插件",
    version="0.1.0",
    author="bingjuu",
    desire_priority=0
)
class ElectricityPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.config = plugin_config.get("electricity_plugin", {})
        self.pending_registrations = {}
        self.account_extractor = AccountExtractor()
        logger.info(f"[ElectricityPlugin] inited, config={self.config}")
        self.start_monitoring()

    def on_handle_context(self, e_context: EventContext):
        if not self.config.get("enabled", True):
            return
        
        context = e_context['context']
        
        if context.type != ContextType.TEXT:
            return

        content = context.content
        logger.debug(f"[ElectricityPlugin] received message: {content}")

        try:
            if context.get('session_id') in self.pending_registrations:
                self._handle_group_registration(e_context)
                return

            if '查电费' in content:
                self._handle_query_request(content, e_context)
            elif '监控电费' in content and '取消' not in content:
                self._handle_monitor_request(content, e_context)
            elif '取消电费监控' in content:
                self._handle_cancel_request(content, e_context)
                
        except Exception as e:
            logger.error(f"[ElectricityPlugin] Error processing message: {str(e)}")
            reply = Reply(ReplyType.TEXT, "处理请求时发生错误，请稍后再试。")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def _handle_query_request(self, content, e_context):
        account = self.account_extractor.extract_account(content)
        if not account:
            reply = Reply(ReplyType.TEXT, "请在消息中包含学号以查询电费。")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        usage_info = ele_usage(account)
        reply = Reply(ReplyType.TEXT, usage_info)
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def _handle_monitor_request(self, content, e_context):
        account = self.account_extractor.extract_account(content)
        if not account:
            reply = Reply(ReplyType.TEXT, "请在消息中包含学号以开启电费监控。")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        session_id = e_context['context'].get('session_id')
        self.pending_registrations[session_id] = account
        
        reply = Reply(ReplyType.TEXT, "请回复您想绑定电费提醒的微信群名称。")
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def _handle_cancel_request(self, content, e_context):
        account = self.account_extractor.extract_account(content)
        if not account:
            reply = Reply(ReplyType.TEXT, "请在消息中包含学号以取消电费监控。")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 调用 remove_account_monitoring 函数
        result = remove_account_monitoring(account)
        
        # 根据返回的 status_code 判断结果
        if result.get("status_code") == 200:
            reply = Reply(ReplyType.TEXT, f"学号 {account} 的电费监控已取消。")
        elif result.get("status_code") == 404:
            reply = Reply(ReplyType.TEXT, f"未找到学号 {account} 的监控记录。")
        else:
            reply = Reply(ReplyType.TEXT, f"取消监控时发生错误: {result.get('message')}")

        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS


    def _handle_group_registration(self, e_context):
        session_id = e_context['context'].get('session_id')
        account = self.pending_registrations[session_id]
        group_name = e_context['context'].get('content').strip()

        if not group_name:
            reply = Reply(ReplyType.TEXT, "群组名称不能为空，请重新输入。")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        response = save_user_num(account, group_name)
        del self.pending_registrations[session_id]
        
        reply = Reply(ReplyType.TEXT, response["message"])
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def start_monitoring(self):
        def monitor_task():
            while True:
                try:
                    accounts, groups, result = load_user_num()
                    if result.get("status_code") == 200:
                        for account, group in zip(accounts, groups):
                            warning = ele_auto(account)
                            if warning:
                                context = {
                                    'type': ContextType.TEXT,
                                    'content': warning,
                                    'kwargs': {
                                        'isgroup': True,
                                        'msg': {
                                            'from_user_nickname': group
                                        }
                                    }
                                }
                                reply = Reply(ReplyType.TEXT, warning)
                                e_context = EventContext(Event.ON_HANDLE_CONTEXT, 
                                                        {'context': context, 'reply': reply})
                                e_context.action = EventAction.BREAK_PASS
                                logger.info(f"[ElectricityPlugin] 已发送预警至群组 {group}")
                except Exception as e:
                    logger.error(f"[ElectricityPlugin] 监控任务出错: {str(e)}")
                finally:
                    time.sleep(self.config.get("check_interval", 10))

        monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        monitor_thread.start()
        logger.info("[ElectricityPlugin] 电费监控线程已启动")

    def get_help_text(self, **kwargs):
        help_text = "电费监控插件使用说明\n"
        help_text += "支持的功能：\n"
        help_text += "1. 查询电费：发送 '查电费 学号'\n"
        help_text += "2. 设置监控：发送 '监控电费 学号'\n"
        help_text += "3. 取消监控：发送 '取消电费监控 学号'\n"
        help_text += "注意事项：\n"
        help_text += "- 请确保输入正确的学号\n"
        help_text += "- 监控设置后会在电费低于阈值时自动提醒\n"
        return help_text

class AccountExtractor:
    def extract_account(self, text):
        match = re.search(r'\d{8,20}', text)
        return match.group() if match else None
