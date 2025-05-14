from api.config import DOMAIN, AUTH, DEFAULT_HEADER

class BaseApi:
    def __init__(self):
        self.domain = DOMAIN
        self.auth = AUTH
        self.default_header = DEFAULT_HEADER

