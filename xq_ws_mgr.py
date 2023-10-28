import time
import asyncio
import websockets

from .log import logger 

class XueQiuWebsocketManager:
    
    def __init__(self, target, action):
        self.target = target
        self.action = action
        logger.info("openning ws...")
        asyncio.get_event_loop().run_until_complete(self.ws_handler)
        asyncio.get_event_loop().run_forever()
        
    async def ws_handler(self):
        while True:
            try:
                async with websockets.connect('ws://127.0.0.1:4000') as websocket:
                    logger.info("ws connected...")
                    while True:
                        try:
                            body_content = await websocket.recv()
                            getattr(self.target, self.action)(body_content)
                        except websockets.WebSocketException.ConnectionClosed as e:
                            await websocket.close()  # Close the WebSocket connection
                            logger.warning("WebSocket disconnected")
                            break
                        except Exception as e:
                            logger.warning(e)
                            break
            except Exception as e:
                logger.warning(e)
                time.sleep(5)