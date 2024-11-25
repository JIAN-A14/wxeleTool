import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *
from config import plugin_config
from common.log import logger

@plugins.register(
    name="group_reply",
    desc="A plugin that replies different messages based on group settings",
    version="0.1.0",
    author="bingjuu",
    desire_priority=0
)
class GroupReply(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        # 从全局配置获取插件配置
        self.config = plugin_config.get("group_reply", {})
        logger.info(f"[GroupReply] inited, config={self.config}")

    def on_handle_context(self, e_context: EventContext):
        """
        处理消息
        :param e_context: 消息上下文
        """
        if not self.config.get("enabled"):
            return
        
        context = e_context['context']
        
        # 只处理文本消息
        if context.type != ContextType.TEXT:
            return
            
        # 判断是否群聊消息
        if not context.kwargs.get("isgroup"):
            return
            
        # 获取群名
        group_name = context.kwargs.get("msg").from_user_nickname
        
        # 获取群组规则
        group_rules = self.config.get("group_rules", {})
        group_config = group_rules.get(group_name)
        if not group_config:
            return
            
        # 判断是否触发关键词
        if context.content == group_config.get("trigger"):
            reply_text = group_config.get("reply", "")
            reply = Reply(ReplyType.TEXT, reply_text)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            
    def get_help_text(self, **kwargs):
        help_text = "基于群组的自动回复插件\n\n"
        help_text += "配置方式：\n"
        help_text += "在 config.json 中的 group_reply 配置项设置群组规则\n"
        return help_text
