
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
    
    def login(self, user=None, password=None, **kwargs):
        """
        雪球登陆， 需要设置 cookies
        :param cookies: 雪球登陆需要设置 cookies， 具体见
            https://smalltool.github.io/2016/08/02/cookie/
        :return:
        """
        cookies = kwargs.get("cookies")
        if cookies is None:
            raise TypeError(
                "雪球登陆需要设置 cookies， 具体见" "https://smalltool.github.io/2016/08/02/cookie/"
            )
        headers = self._generate_headers()
        self.s.headers.update(headers)
        print(self.LOGIN_PAGE)
        for _ in range(0, 10):
            print(_)
            try:
                self.s.get(self.LOGIN_PAGE)
                break
            except Exception as e:
                print(e)
                time.sleep(60)

        cookie_dict = parse_cookies_str(cookies)
        self.s.cookies.update(cookie_dict)
        logger.info("登录成功")
        print("login suc")        

    def extract_strategy_name(self, strategy_url):
        base_url = "https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol={}"
        url = base_url.format(strategy_url)
        print(url)
        rep = self.s.get(url)
        return rep

    def _get_portfolio_info(self, portfolio_code):
        url = self.PORTFOLIO_URL + portfolio_code
        print(url)
        for _ in range(10):
            try:
                resp = self.s.get(url, timeout=3)
                return resp
            except Exception as e:
                with Myqq.Myqq() as myqq:
                    myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)
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
        