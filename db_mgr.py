import os
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import pooling

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class DbMgr(metaclass=SingletonMeta):
    _instance = None

    def __init__(self):
        self.initialize()

    def initialize(self):
        load_dotenv()  # 加载 .env 文件中的配置
        self.db_pool = pooling.MySQLConnectionPool(
            pool_name="db_pool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
            auth_plugin=os.getenv("DB_AUTH_PLUGIN")
        )

    def mark_as_read(self, msg_id):
        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute('update xqp set isread = 1 where messageId=%s;', (msg_id,))
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()

    def keep_alive(self):
        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("select * from xueqiu.xqp where id=1;")
            cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
    
    def _get_trading_trades(self, _is_trading):
        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        sql = f'select view, ID, insert_time,messageID from xueqiu.xqp where isread = 0 and is_trading = {_is_trading} order by ID asc;'
        cursor.execute(sql)
        myresult = cursor.fetchall()
        cursor.close()
        connection.commit()
        return myresult

    def mark_xqp_as_done(self, id):
        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        self.cursor = cursor
        self.connection = connection
        _sql = "update xueqiu.xqp SET `isread`=1 WHERE ID = '%d';" % id
        print(_sql)
        cursor.execute(_sql)
        
    def commit(self):
        self.cursor.close()
        self.connection.commit()

    def _read_config(self):
        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        cursor.execute('select id,zh,host,cap0,cn from xueqiu.zh_conf_zhconf')
        myresult = cursor.fetchall()
        configs = []
        for x in myresult:
            (ID, ZH, host, cap0, cn) = x
            configs.append({
                "ID": ID,
                "ZH": ZH,
                "host": host,
                "cap0": cap0,
                "cn": cn
            })
        cursor.close()
        connection.commit()
        return configs