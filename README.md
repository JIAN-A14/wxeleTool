# **完美校园电费💡查询，监控和低电量预警插件**
QQ的有人做了，但是似乎没人做微信版本的插件，于是在使用微信的电费插件就诞生了<br>
这是[chatgpt on wechat](https://github.com/zhayujie/chatgpt-on-wechat)（以下简称cow）使用的关于完美校园电费查询和警告的插件，理论上兼容itchat和wechaty（但最好还是用cow）<br>



# **省流食用教程 👇**
1.在自己的电脑或者服务器上部署[chatgpt on wechat](https://github.com/zhayujie/chatgpt-on-wechat)，部署教程参考cow<br>
2.将整个文件夹丢到chatgpt-on-wechat/plugins中<br>
3.将配置文件模板config.json.template复制粘贴到同一目录并将名字改成config.json,然后填写配置文件（config.json）中的customercode（通常为4位数），你需要知道你学校的customercode，可以通过抓包和在[完美校园查询](https://open.17wanxiao.com/kdword_fl02.html)<br>
文件夹里有一个test_customercode.py脚本，用来测试你获取到的customercode是否正确，只需将code填入配置文件config中并允许脚本即可<br>
4.运行cow并向机器人发送#help wxeleTool获取教程<br>



# **配置文件列表（配置文件是本目录里的config.json）👇**
customercode（学校代码）: 一个学校对应一个学校代码，请自行查询<br>
warningswitch（告警和提醒切换）:（填写true为仅告警模式，到了设定的低电量才会发消息;填写false为提醒，无论是否有电都会向群发送电量信息和提醒）<br>
warnnum（低电量阈值）： 填写数字，自由设定低电量的阈值（填写20代表电量低于20度会发送警告）<br>
checkinterval(检测和提醒间隔) ： 单位是秒，一小时就填3600<br>



# **实现功能 👇**
✅查询电费: 发送包含'电费'和'查'的消息（消息包含关键字即可），并附上学号<br>
✅监控电费: 发送包含'电费'和'监控'的消息（同上），并附上学号，根据引导填写要绑定的微信群名<br>
✅取消监控: 发送包含'取消电费监控'的消息（同上），并附上学号<br>

---
 <strong style="font-size: 24px;">如果这个插件对你有所帮助，请给我点一个star⭐，非常感谢</strong>