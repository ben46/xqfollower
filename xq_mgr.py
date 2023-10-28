
import time
from .utils.misc import parse_cookies_str
from .log import logger

class XqMgr:
    LOGIN_PAGE = "https://www.xueqiu.com"
    LOGIN_API = "https://xueqiu.com/snowman/login"
    TRANSACTION_API = "https://xueqiu.com/cubes/rebalancing/history.json"
    PORTFOLIO_URL = "https://xueqiu.com/p/"
    WEB_REFERER = "https://www.xueqiu.com"
    
    def __init__(self, logger):
        pass
        self.logger = logger
    
    def login(self, **kwargs):
        """
        雪球登录，需要设置 cookies。具体见 https://smalltool.github.io/2016/08/02/cookie/
        :param cookies: 雪球登录所需的 cookies 字符串
        :return: None
        """
        cookies = kwargs.get("cookies")

        if cookies is None:
            raise ValueError("雪球登录需要设置 cookies，具体见 https://smalltool.github.io/2016/08/02/cookie/")
        
        # 设置请求头
        headers = self._generate_headers()
        self.s.headers.update(headers)
        
        # 尝试登录，最多重试 10 次
        for _ in range(10):
            print(f"Attempt {_ + 1}")
            try:
                self.s.get(self.LOGIN_PAGE)
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

        # 更新 cookies
        cookie_dict = parse_cookies_str(cookies)
        self.s.cookies.update(cookie_dict)

        logger.info("登录成功")

    def extract_strategy_name(self, strategy_url):
        base_url = "https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol={}"
        url = base_url.format(strategy_url)
        print(url)
        rep = self.s.get(url)
        print(rep)
        info_index = 0
        return rep.json()[info_index]["name"]

    def _get_portfolio_info(self, portfolio_code):
        """
        这段代码的功能是获取指定组合（portfolio）的信息。具体功能包括：
        1. 构建请求URL：根据给定的组合代码（portfolio_code）构建用于获取组合信息的URL。
        2. 发送HTTP请求：使用Python的 requests 库发送HTTP GET请求，以获取与给定URL相关的响应。
        3. 从响应中提取组合信息：通过使用正则表达式，从HTTP响应的文本内容中提取组合信息（JSON格式数据），该信息通常包含在文本中的 "SNB.cubeInfo = " 之后，以及分号之前的部分。
        4. 解析JSON数据：尝试将提取的JSON数据解析为Python字典。如果解析失败，会引发异常。
        5. 返回组合信息：如果成功获取并解析组合信息，将其作为字典返回。
        6. 处理异常情况：如果在获取组合信息的过程中出现任何异常，会记录异常信息并等待10秒后进行重试，最多重试10次。
        此代码的主要目的是通过HTTP请求从特定URL获取组合信息，然后将其以字典形式返回。如果无法成功获取组合信息，将记录异常信息。
        """
        url = self.PORTFOLIO_URL + portfolio_code
        print(url)
        for _ in range(10):
            try:
                resp = self.s.get(url, timeout=3)
                return resp
            except Exception as e:
                # TODO 
                # send exception email through flask api
                # myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)
                print('cookie可能过期了')
                print('fetch fail try 10s later')
                time.sleep(10)
                
    def create_query_transaction_params(self, strategy):
        params = {"cube_symbol": strategy, "page": 1, "count": 2}
        return params
    
    def query_strategy_transaction(self, strategy):
        params = self.create_query_transaction_params(strategy)
        rep = self.s.get(self.TRANSACTION_API, params=params)
        history = rep.json()
        return history
    
    def _generate_headers(self):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/54.0.2840.100 Safari/537.36",
            "Referer": self.WEB_REFERER,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.WEB_ORIGIN,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        return headers
        