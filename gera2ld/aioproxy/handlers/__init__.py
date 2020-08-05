from gera2ld.socks.server.config import Config
from .http import HTTPProxyHandler
from .socks import SOCKSProxyHandler

def create_handler(socks_proxy=None):
    config = Config()
    config.set_proxies([(None, socks_proxy)])
    http_handle = HTTPProxyHandler(socks_proxy)
    socks_handle = SOCKSProxyHandler(config)
    async def handle(reader, writer):
        feed = await reader.readexactly(1)
        handle_request = socks_handle if feed in b'\4\5' else http_handle
        await handle_request(reader, writer, feed)
    return handle
