import logging
import time

from gera2ld.pyserve import Host
from gera2ld.socks.server import SOCKS4Handler, SOCKS5Handler, UDPRelayServer

handler_map = {
    4: SOCKS4Handler,
    5: SOCKS5Handler,
}
udp_server = UDPRelayServer()


async def handle(reader, writer, config, feed=b''):
    start_time = time.time()
    if not feed:
        feed = await reader.readexactly(1)
    version, = feed
    Handler = handler_map[version]
    handler = Handler(reader, writer, config, udp_server)
    name, len_local, len_remote, _error = await handler.handle()
    proxy = handler.config.get_proxy(handler.addr[0], handler.addr[1],
                                     handler.addr[0])
    proxy_log = ' X' + str(proxy) if proxy else ''
    logging.info('SOCKS %s:%s%s %.3fs <%d >%d', name,
                 Host(handler.addr).host, proxy_log,
                 time.time() - start_time, len_local, len_remote)
