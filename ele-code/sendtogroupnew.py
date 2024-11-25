from bridge.reply import Reply, ReplyType
from common.log import logger
from .eledef import ele_usage, ele_auto, save_user_num, load_user_num,remove_account_monitoring

def send_to_group(self,groupid,account):
    if context.type != ContextType.TEXT:
            return 
    
    if not context.kwargs.get("isgroup"):
        return 

    group_name = context.kwargs.get("msg").from_user_nickname
    
    reply_text = ele_auto(account)
    


    # 创建回复消息
    reply_text = Reply(ReplyType.TEXT, groupid)

    # 模拟发送消息到群组
    try:
        # 假设这里是直接发送消息的逻辑
        # 具体实现依赖于项目中的发送机制，例如调用某个方法发送消息
        logger.info(f"[GroupReply] 消息已发送到群组 '{group_name}': {message_content}")
    except Exception as e:
        logger.error(f"[GroupReply] 发送消息到群组 '{group_name}' 失败: {e}")
