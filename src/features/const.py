# const.py - 百度实时语音识别配置
import uuid

APPID = 121481135
APPKEY = 'ESCpu3gBRYKa8lIie0mkj2Ce'
SECRET_KEY = "QNHr3bl84RSldoPmanBI7Jg2OPBgKLCy"
DEV_PID = 15372  # 普通话输入法模型
URI = f"wss://vop.baidu.com/realtime_asr?sn={str(uuid.uuid1())}"

