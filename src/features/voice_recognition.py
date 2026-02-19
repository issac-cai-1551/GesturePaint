import json
import uuid

import requests
import speech_recognition as sr
import websocket
from aip import AipSpeech
import time
from .const import APPID,APPKEY,DEV_PID,URI,SECRET_KEY
import pyaudio
import threading
import time



class BaiduRealtimeASR:
    """
    百度实时语音识别的音频处理核心类。
    职责：管理音频设备，持续采集麦克风数据，并通过回调函数输出。
    """

    def __init__(self, audio_callback):
        """
        初始化音频采集器
        :param audio_callback: 音频数据回调函数，接收一个参数：音频二进制数据 (bytes)
        """
        self.audio_callback = audio_callback
        self.is_listening = False
        self.audio_thread = None

        # 音频参数 **必须与百度要求严格一致**
        self.FORMAT = pyaudio.paInt16  # 16位深度
        self.CHANNELS = 1  # 单声道
        self.RATE = 16000  # 16kHz采样率
        self.CHUNK = 5120  # 每次读取的帧大小（对应80ms音频）

        # PyAudio实例和流
        self.p = None
        self.stream = None

        self._setup_audio()

    def _setup_audio(self):
        """初始化PyAudio和音频流"""
        try:
            self.p = pyaudio.PyAudio()

            # 测试并选择正确的输入设备（可选，但更健壮）
            default_input = self.p.get_default_input_device_info()
            print(f"✅ 使用默认音频输入设备: {default_input['name']}")

        except Exception as e:
            print(f"❌ 初始化音频设备失败: {e}")
            raise

    def _audio_loop(self):
        """音频采集循环（在新线程中运行）"""
        print("🎤 音频采集线程启动")
        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=None,  # 使用阻塞模式
                input_device_index=None  # 使用默认设备
            )

            while self.is_listening:
                # 从麦克风读取数据（阻塞调用）
                try:
                    audio_data = self.stream.read(
                        self.CHUNK,
                        exception_on_overflow=False  # 重要：避免输入溢出时崩溃
                    )

                    # 将音频数据通过回调函数发送出去
                    if self.audio_callback and audio_data:
                        self.audio_callback(audio_data)

                    # 重要：根据CHUNK大小计算需要sleep的时间
                    # 80ms的数据块需要间隔80ms发送
                    time.sleep(0.16)  # 80ms


                except IOError as e:
                    # 处理音频读取出错
                    if self.is_listening:  # 仅在监听状态下报告错误
                        print(f"⚠️  音频读取错误: {e}")
                        time.sleep(0.01)

        except Exception as e:
            print(f"🔴 音频循环异常: {e}")
        finally:
            self._close_audio_stream()
            print("🛑 音频采集线程结束")

    def _close_audio_stream(self):
        """安全关闭音频流"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except:
                pass

    def start(self):
        """开始采集音频"""
        if self.is_listening:
            print("⚠️  音频采集已在运行")
            return

        self.is_listening = True
        # 在新线程中启动音频循环，避免阻塞主线程
        self.audio_thread = threading.Thread(target=self._audio_loop)
        self.audio_thread.daemon = True  # 设置为守护线程
        self.audio_thread.start()
        print("✅ 音频采集已开始")

    def stop(self):
        """停止采集音频"""
        if not self.is_listening:
            return

        self.is_listening = False
        print("正在停止音频采集...")

        # 等待音频线程结束（最多等2秒）
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)

        self._close_audio_stream()
        print("✅ 音频采集已停止")

    def cleanup(self):
        """完全清理资源"""
        self.stop()

        if self.p:
            try:
                self.p.terminate()
                self.p = None
            except:
                pass
        print("🧹 音频资源已清理")

    def get_audio_params(self):
        """获取音频参数（用于WebSocket START帧）"""
        return {
            "sample": self.RATE,
            "format": "pcm",  # 百度API要求的参数名
            "channel": self.CHANNELS
        }

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup()

class RealtimeVoiceController:
    def __init__(self, on_result_callback=None):
        """
        :param on_result_callback: 识别结果回调函数
        """
        self.on_result_callback = on_result_callback
        self.ws_app = None
        self.ws_connected = False
        self.access_token = None
        self.sn = None


        # 先获取Access Token
        self._get_access_token()

        # 创建音频处理器实例，传入音频数据回调
        self.audio_processor = BaiduRealtimeASR(
            audio_callback=self._on_audio_data_received
        )

    def _get_access_token(self):
        """获取百度语音识别的Access Token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": APPKEY,
            "client_secret": SECRET_KEY
        }

        try:
            print("🔑 正在获取Access Token...")
            response = requests.post(url, params=params, timeout=10)
            result = response.json()

            if "access_token" in result:
                self.access_token = result["access_token"]
                print(f"✅ Token获取成功: {self.access_token[:20]}...")
            else:
                print(f"❌ Token获取失败: {result}")
                self.access_token = None
        except Exception as e:
            print(f"❌ 请求Token异常: {e}")
            self.access_token = None

    def _generate_uri(self):
        """生成WebSocket连接URI（按照官方文档格式）"""
        if not self.access_token:
            print("❌ 没有有效的Access Token")
            return None

        # 生成SN参数（随机UUID）
        self.sn = str(uuid.uuid4())

        # 按照文档格式构造URI
        uri = f"wss://vop.baidu.com/realtime_asr?sn={self.sn}&access_token={self.access_token}"
        print(f"🔗 生成WebSocket URI: {uri}")
        return uri

    def _on_audio_data_received(self, audio_data):
        """
        接收到音频数据时的回调函数
        """
        # 调试点1：确认回调是否被触发
        # print(f"[调试] 收到音频数据块，长度: {len(audio_data)}") # 可以先注释，太吵

        if not self.ws_connected:
            # 调试点2：检查连接状态
            print(f"⚠️  收到音频数据，但连接状态 ws_connected=False，无法发送。")
            return

        if not self.ws_app:
            # 调试点3：检查ws_app对象是否存在
            print(f"❌ 致命：收到音频数据，但 self.ws_app 为 None！")
            return

        # 尝试发送
        try:
            self.ws_app.send(audio_data, websocket.ABNF.OPCODE_BINARY)
            # 调试点4：确认发送成功（偶尔打印，避免刷屏）
            # if random.random() < 0.01: # 例如每秒打印几次
            #     print(f"[调试] 音频数据已成功发送")
        except websocket.WebSocketConnectionClosedException:
            print("🚫 发送失败：WebSocket连接已关闭")
            self.ws_connected = False
        except Exception as e:
            # 捕获其他可能异常
            print(f"🚫 发送音频数据时出现意外错误: {type(e).__name__}: {e}")

    def on_open(self, ws):
        """WebSocket连接成功回调（终极测试版）"""
        print("✅ WebSocket连接已建立")
        self.ws_connected = True
        self.ws_app = ws

        # 1. 发送START参数帧 (与官方Demo完全一致)
        start_req = {
            "type": "START",
            "data": {
                "appid": APPID,
                "appkey": APPKEY,
                "dev_pid": DEV_PID,
                "cuid": str(uuid.uuid4()),  # 用户唯一标识
                "format": "pcm",
                "sample": 16000
            }
        }

        # 如果是中文多方言模型，需要添加user参数
        if DEV_PID == 15372:
            start_req["data"]["user"] = "user123"

        body = json.dumps(start_req)
        ws.send(body, websocket.ABNF.OPCODE_TEXT)
        print("📨 START帧已发送:", body)

        # 启动真正的麦克风音频采集
        self.audio_processor.start()

    def on_message(self, ws, message):
        """处理服务器返回的识别结果"""
        try:
            result = json.loads(message)

            # 检查错误码
            if result.get("err_no") != 0:
                err_msg = result.get("err_msg", "未知错误")
                print(f"❌ 识别错误 [{result.get('err_no')}]: {err_msg}")
                return

            # 获取结果类型
            result_type = result.get("type", "")

            if result_type == "MID_TEXT":
                # 临时识别结果
                text = result.get("result", "")
                print(f"🟡 正在识别: {text}", end='\r')

            elif result_type == "FIN_TEXT":
                # 最终识别结果
                text = result.get("result", "")
                start_time = result.get("start_time", 0)
                end_time = result.get("end_time", 0)

                print(f"\n✅ 最终结果: {text}")
                print(f"   ⏱️  开始时间: {start_time}ms, 结束时间: {end_time}ms")

                # 调用回调函数处理结果
                if self.on_result_callback:
                    self.on_result_callback(text, start_time, end_time)

            elif result_type == "HEARTBEAT":
                # 心跳帧，忽略
                pass

            else:
                print(f"📨 收到消息: {result}")

        except json.JSONDecodeError:
            print(f"收到非JSON消息: {message[:100]}")
        except Exception as e:
            print(f"处理消息时出错: {e}")

    def on_error(self, ws, error):
        """WebSocket错误回调"""
        print(f"🔴 WebSocket错误: {error}")
        self.ws_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket连接关闭回调"""
        print(f"连接关闭: code={close_status_code}, msg={close_msg}")
        self.ws_connected = False

        # 停止音频采集
        self.audio_processor.stop()

    def start(self):
        """启动整个语音识别系统"""
        print("🚀 启动语音识别控制器...")

        if not self.access_token:
            print("❌ 无法启动：缺少有效的Access Token")
            return

        # 创建WebSocket连接
        self.ws_app = websocket.WebSocketApp(
            url=self._generate_uri(),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        # 可以启用跟踪调试
        # websocket.enableTrace(True)

        # 运行WebSocket（会阻塞）
        try:
            self.ws_app.run_forever()
        except Exception as e:
            print(f"🔴 WebSocket运行异常: {e}")

    def stop(self):
        """停止整个系统"""
        print("🛑 正在停止语音识别系统...")

        # 停止音频采集
        self.audio_processor.stop()

        # 发送FINISH帧（如果还连接着）
        if self.ws_connected and self.ws_app:
            finish_req = {"type": "FINISH"}
            try:
                self.ws_app.send(json.dumps(finish_req), websocket.ABNF.OPCODE_TEXT)
                print("📨 FINISH帧已发送")
                time.sleep(0.5)  # 等待服务端处理
            except Exception as e:
                print(f"发送FINISH帧失败: {e}")

        # 关闭WebSocket
        if self.ws_app:
            self.ws_app.close()

        self.ws_connected = False
        print("✅ 系统已停止")

    def cleanup(self):
        """清理所有资源"""
        self.stop()
        self.audio_processor.cleanup()

    def manual_finish(self):
        """用户主动结束录音并获取最终结果"""
        if self.ws_connected and self.ws_app:
            finish_req = {"type": "FINISH"}
            try:
                self.ws_app.send(json.dumps(finish_req), websocket.ABNF.OPCODE_TEXT)
                print("🗣️ 用户主动结束，FINISH帧已发送")
            except Exception as e:
                print(f"发送FINISH帧失败: {e}")


def main():
        print("=" * 50)
        print("百度实时语音识别系统")
        print("=" * 50)

        # 定义结果回调函数
        def on_result(text, start_time, end_time):
            print(f"\n🎯 识别结果回调:")
            print(f"   文本: {text}")
            print(f"   时间: {start_time}ms - {end_time}ms")
            # 这里可以添加您的业务逻辑

        # 创建控制器
        controller = RealtimeVoiceController(on_result_callback=on_result)

        try:
            controller.start()
        except KeyboardInterrupt:
            print("\n\n👋 用户中断")
        except Exception as e:
            print(f"\n\n🔥 程序异常: {e}")
        finally:
            controller.cleanup()
            print("\n🏁 程序结束")

if __name__ == "__main__":
        main()