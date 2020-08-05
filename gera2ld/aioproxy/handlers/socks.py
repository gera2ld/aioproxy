import logging
import time
from gera2ld.pyserve import Host
from gera2ld.socks.server import SOCKS4Handler, SOCKS5Handler

class SOCKSProxyRequest:
    handler_map = {
        4: SOCKS4Handler,
        5: SOCKS5Handler,
    }

    def __init__(self, handler, reader, writer):
        self.reader = reader
        self.writer = writer
        self.handler = handler

    async def handle(self, feed=b''):
        start_time = time.time()
        if not feed:
            feed = await self.reader.readexactly(1)
        version, = feed
        Handler = self.handler_map[version]
        handler = Handler(self.reader, self.writer, self.handler.config, None)
        _name, len_local, len_remote, _error = await handler.handle()
        proxy = handler.config.get_proxy(host=handler.addr[0], port=handler.addr[1], hostname=handler.addr[0])
        proxy_log = ' X' + str(proxy) if proxy else ''
        logging.info('SOCKS %s%s %.3fs <%d >%d', Host(handler.addr).host, proxy_log, time.time() - start_time, len_local, len_remote)

class SOCKSProxyHandler:
    def __init__(self, config):
        self.config = config
        self.connections = set()

    async def __call__(self, reader, writer, feed=b''):
        request = SOCKSProxyRequest(self, reader, writer)
        self.connections.add(request)
        try:
            await request.handle(feed)
        finally:
            self.connections.discard(request)
