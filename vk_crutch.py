import time
import json
import requests
from user_agent import generate_user_agent
import lxml.html as html

class AuthorizationError(Exception): pass

class VkApiCrutch:
    api_ver = None
    user_agent = None
    __session__ = None

    def __init__(self, login = None, password = None, user_agent = None, api_ver = '5.92'):
        self.login = login
        self.password = password
        self.api_ver = api_ver

        if user_agent is None:
            self.user_agent = str(generate_user_agent())
        else:
            self.user_agent = str(user_agent)

    def auth(self):
        if self.login is None:
            raise AuthorizationError('No login')
        elif self.password is None:
            raise AuthorizationError('No password')

        session = requests.Session()
        data = session.get('https://m.vk.com').text
        data_text = html.fromstring(data)
        action = data_text.xpath('//form[@method="post"]/@action')[0]
        auth = session.post(action, data = {'email': self.login, 'pass': self.password})

        if str(auth.url) == 'https://m.vk.com/':
            self.__session__ = session
        elif str(auth.url) == 'https://m.vk.com/login?role=fast&to=&s=1&m=1&email=' + str(login):
            raise AuthorizationError('Please check the correctness of the entered data.')
        elif str(auth.url) == 'https://m.vk.com/login?act=authcheck':
            raise AuthorizationError('This page uses two-factor authentication, for authorization please disable two-factor authentication')
        elif str(auth.url).split('?')[1].split('&')[4] == 'dif=2':
            raise AuthorizationError('This page asks you to enter Captcha, please try again later.')
        return True

    def request_method(self, method, payload):
        headers = {
            "accept": '*/*',
            "accept-encoding": 'gzip, deflate, br',
            "accept-language": 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6,it;q=0.5',
            "content-type": 'application/x-www-form-urlencoded',
            "User-Agent": self.user_agent,
            "x-requested-with": 'XMLHttpRequest'
        }

        params = {}

        default_params = {
            'act': 'a_run_method',
            'al': '1',
            'hash': str(self._get_hash_(method)),
            'method': str(method)
        }

        for key in payload:
            if not str(key) == 'access_token':
                params['param_' + str(key)] = str(payload[str(key)])

        params['param_v'] = self.api_ver

        for key in default_params:
            params[str(key)] = str(default_params[str(key)])

        data = self.__session__.post('https://vk.com/dev', headers = headers, data = params)
        return json.loads(data.text.split('<!>')[5])

    def _get_hash_(self, method):
        headers = {
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6,it;q=0.5',
            'User-Agent': self.user_agent,
            'x-requested-with': 'XMLHttpRequest'
        }
        data = self.__session__.get('https://vk.com/dev/' + str(method), headers = headers)
        data = html.fromstring(data.text)
        data_hash = data.xpath('//button[@id="dev_req_run_btn"]/@onclick')[0].split(',')[0].split('(')[1].replace("'", '')
        return str(data_hash)
