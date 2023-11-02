import time
import socketio

from .log import logger 
from .time_utils import is_off_trading_hour

class XueQiuWebsocketManager:
    
    def __init__(self, target, action):
        self.target = target
        self.action = action
        logger.info("openning ws...")
        # 创建 Socket.IO 客户端
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=999, reconnection_delay=5)
        self.sio.connect('http://localhost:3000')
        
        # 当连接建立时的事件处理函数
        @self.sio.on('connect')
        def on_connect():
            logger.info('已连接到服务器')

        # 当收到广播消息时的事件处理函数
        @self.sio.on('broadcast_message')
        def on_broadcast_message(data):
            logger.info(f'收到广播消息：{data}')
            if is_off_trading_hour():
                self.sio.emit('special_message', data)
            else:
                getattr(self.target, self.action)(data)
                
        # 当收到特定消息时的事件处理函数
        @self.sio.on('consumed_message')
        def on_consumed_message(data):
            logger.info(f'消费特定消息：{data}')
            getattr(self.target, self.action)(data)
    
    # 发送消息到服务端
    def send_message(self,message):
        self.sio.emit('message', message)

    # 发送特定消息到服务端
    def send_special_message(self,message):
        self.sio.emit('special_message', message)

    # 查询特定消息
    def query_special_messages(self):
        self.sio.emit('query_special_messages')

    # 消费特定消息
    def consume_special_messages(self):
        self.sio.emit('consume_special_messages')