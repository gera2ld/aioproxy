from gera2ld.socks.server.config import Config
from .http import handle as handle_http
from .socks import handle as handle_socks

def create_handler(socks_proxy=None):
    config = Config()
    config.set_proxies([(None, socks_proxy)])
    async def handle(reader, writer):
        feed = await reader.readexactly(1)
        if feed in b'\4\5':
            await handle_socks(reader, writer, config, feed)
        else:
            await handle_http(reader, writer, socks_proxy, feed)
    return handle
