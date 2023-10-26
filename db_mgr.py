
import os
import mysql.connector
from dotenv import load_dotenv

class DbMgr:
    
    def __init__(self):
        load_dotenv()  # 加载 .env 文件中的配置
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_database = os.getenv("DB_DATABASE")
        self.db_auth_plugin = os.getenv("DB_AUTH_PLUGIN")
        self.db = self._make_mysql_connect()

    def _make_mysql_connect(self):
        mydb = mysql.connector.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_database,
            auth_plugin=self.db_auth_plugin
        )
        self.cursor = mydb.cursor()
        return mydb

    def mark_as_read(self, msg_id):
        self.db = self._make_mysql_connect()
        self.cursor = self.db.cursor()
        self.cursor.execute('update xqp set isread = \'1\' where messageId=\'%s\';' % msg_id)
        self.db.commit()
        self.db.close()
        
    def keep_alive(self):
        self.cursor = self.db.cursor()
        self.cursor.execute("select * from xueqiu.xqp where id=1;")
        self.cursor.fetchall()

    def close(self):
        self.db.close()
    
    def _get_trading_trades(self, _is_trading):
        sql = f'select view, ID, insert_time,messageID from xueqiu.xqp where isread = 0 and is_trading = {_is_trading} order by ID asc;'
        self.cursor = self.db.cursor()
        self.cursor.execute(sql)
        myresult = self.cursor.fetchall()
        self.cursor.close()
        self.db.commit()
        return myresult

    def mark_xqp_as_done(self, id):
        self.cursor = self.db.cursor()
        _sql = "update xueqiu.xqp SET `isread`=1 WHERE ID = '%d';" % id
        print(_sql)
        self.cursor.execute(_sql)

    def commit(self):
        self.cursor.close()
        self.db.commit()

    def _read_config(self):
        mydb = self._make_mysql_connect()
        self.cursor = mydb.cursor()
        self.cursor.execute('select id,zh,host,cap0,cn from xueqiu.zh_conf_zhconf')
        myresult = self.cursor.fetchall()
        for x in myresult:
            (ID, ZH, host, cap0, cn) = x
            self.configs.append({
                "ID": ID,
                "ZH": ZH,
                "host": host,
                "cap0": cap0,
                "cn": cn
            })
        self.cursor.close()
        mydb.commit()
        mydb.close()