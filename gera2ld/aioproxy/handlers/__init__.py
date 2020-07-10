from aiohttp import web
from .connect import handle as handle_connect
from .proxy import handle as handle_proxy

class Handler:
    def __init__(self, socks_proxy=None):
        self.socks_proxy = socks_proxy

    async def __call__(self, request):
        if request.method == 'CONNECT':
            return await handle_connect(self, request)
        if '://' in request.raw_path:
            return await handle_proxy(self, request)
        if request.method not in ('HEAD', 'GET'):
            raise web.HTTPMethodNotAllowed
        raise web.HTTPNotFound
