import datetime
import json
import time
from queue import Queue
import mysql.connector
import websockets
import asyncio
from threading import Thread

class SKT_ClientTrader():
    ws = None
    def __init__(self, _domain, _mydb, environ):
        self.domain = _domain
        self.mydb = mysql.connector.connect(
            host=environ['host'],
            user=environ['user'],
            password=environ['password'],
            database=environ['database'],
        )
        self.queue = Queue()
        strategy_worker = Thread(
            target=self.start_thread,
        )
        strategy_worker.start()


    def start_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  # <----
        # asyncio.ensure_future(foo(loop))
        # loop.run_forever()
        # asyncio.add
        asyncio.get_event_loop().run_until_complete(self.hello())
        asyncio.get_event_loop().run_forever()

    async def hello(self):
        while 1:
            async with websockets.connect(
                    'ws://127.0.0.1:4000') as websocket:
                try:
                    print("ws connected")
                    self.ws = websocket
                    while True:
                        cmd = self.queue.get()
                        await self.ws.send(json.dumps({
                            "type": 2,
                            "data": cmd
                        }))
                        if cmd['action'] == 'buy':
                            self.consume_buy(cmd)
                        else:
                            self.consume_sell(cmd)
                except websockets.ConnectionClosed:
                    await websocket.close()  # Close the WebSocket connection
                    print("try reconnect...")
                    time.sleep(5)
                except:
                    pass
    def consume_buy(self,cmd):
        hash = cmd['hash']
        mycursor = self.mydb.cursor()
        my_sql = "SELECT count(*) FROM xueqiu.xq where hash=\'%s\' and host=\'%s\'" % (hash, self.domain)
        print(my_sql)
        mycursor.execute(my_sql)
        rs = mycursor.fetchall()
        print(rs)
        mycursor.close()
        self.mydb.commit()
        if rs[0][0] != 0:
            return

        mycursor = self.mydb.cursor()
        now = datetime.datetime.now()
        now_time_str = now.strftime("%m/%d/%Y, %H:%M:%S.%f")
        val = (self.domain, "buy", cmd['security'], cmd['price'], cmd['amount'], now_time_str, 0, hash)
        sql = "INSERT INTO xq (host, action, sec, price, amount, insert_time, isread, hash) VALUES (\'%s\', \'%s\', \'%s\', \'%.2f\', " \
              "\'%d\', \'%s\', \'%d\',  \'%s\') ;" % val
        print(sql)
        mycursor.execute(sql)
        mycursor.close()
        self.mydb.commit()
    def consume_sell(self,cmd):
        hash = cmd['hash']
        mycursor = self.mydb.cursor()
        my_sql = "SELECT count(*) FROM xueqiu.xq where hash=\'%s\' and host=\'%s\'" % (hash, self.domain)
        # print(my_sql)
        mycursor.execute(my_sql)
        rs = mycursor.fetchall()
        # print(rs)
        mycursor.close()

        # self.mydb.commit()
        if rs[0][0] != 0:
            return

        mycursor = self.mydb.cursor()
        now = datetime.datetime.now()
        now_time_str = now.strftime("%m/%d/%Y, %H:%M:%S.%f")
        val = (self.domain, "sell", cmd['security'], cmd['price'], cmd['amount'], now_time_str, 0, hash)
        sql = "INSERT INTO xq (host, action, sec, price, amount, insert_time, isread, hash) VALUES (\'%s\', \'%s\', \'%s\', \'%.2f\', " \
              "\'%d\', \'%s\', \'%d\',  \'%s\') ;" % val
        # print(sql)
        # print('insert sell')
        # print(security, price, amount)
        # print(type(security), type(price), type(amount))
        mycursor.execute(sql)
        mycursor.close()
        self.mydb.commit()
    def get_domain(self):
        return self.domain

    def test(self):
        return

    def buy(self, security, price, amount, **kwargs):
        cmd = {
            'security': security,
            'host': self.domain,
            'action': 'buy',
            'price': price,
            'amount': amount,
            'hash': kwargs['hash']
        }
        self.queue.put(cmd)

    def sell(self, security, price, amount, **kwargs):
        cmd = {
            'security': security,
            'host': self.domain,
            'action': 'sell',
            'price': price,
            'amount': amount,
            'hash': kwargs['hash']
        }
        self.queue.put(cmd)


