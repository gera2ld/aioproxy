from aiohttp import web
from .connect import handle as handle_connect
from .proxy import handle as handle_proxy

async def handle(request):
    if request.method == 'CONNECT':
        return await handle_connect(request)
    if '://' in request.raw_path:
        return await handle_proxy(request)
    if request.method not in ('HEAD', 'GET'):
        raise web.HTTPMethodNotAllowed
    raise web.HTTPNotFound
