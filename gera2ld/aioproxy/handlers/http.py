import asyncio
import logging
import io
import time
from urllib import parse
from gera2ld.pyserve import Host
from gera2ld.socks.client import create_client
from gera2ld.socks.utils import forward_pipes

logger = logging.getLogger(__package__)

async def read_headers(reader):
    while True:
        line = await reader.readuntil(b'\n')
        if line == b'\r\n' or not line: break
        yield line

async def send_headers(writer, headers):
    for key, value in headers:
        writer.write(key)
        writer.write(b': ')
        writer.write(value)
        writer.write(b'\r\n')

async def send_request(writer, path, method=b'GET', protocol=b'HTTP/1.1', headers=None):
    writer.write(method)
    writer.write(b' ')
    writer.write(path)
    writer.write(b' ')
    writer.write(protocol)
    writer.write(b'\r\n')
    if headers:
        await send_headers(writer, headers)
    writer.write(b'\r\n')
    await writer.drain()

async def send_response(writer, protocol=b'HTTP/1.1', status=200, message=b'OK', headers=None):
    writer.write(protocol)
    writer.write(f' {status} '.encode())
    writer.write(message)
    writer.write(b'\r\n')
    if headers:
        await send_headers(writer, headers)
    writer.write(b'\r\n')
    await writer.drain()

class HTTPProxyRequest:
    def __init__(self, handler, reader, writer):
        self.reader = reader
        self.writer = writer
        self.handler = handler
        self.remote = None

    async def handle(self, feed=b''):
        reader = self.reader
        writer = self.writer
        first_line = feed + await reader.readuntil(b'\n')
        initial_len = len(first_line)
        method, path, protocol = first_line.strip().split(b' ', 3)
        headers = []
        async for line in read_headers(self.reader):
            initial_len += len(line)
            key, _, value = line.strip().partition(b':')
            if value is None: value = b''
            headers.append((key.strip().lower(), value.strip()))
        logger.debug('headers: %s', headers)
        start_time = time.time()
        path = path.decode()
        try:
            if method == b'CONNECT':
                len_local, len_remote = await self.handle_connect(method, path, protocol, headers)
            else:
                len_local, len_remote = await self.handle_proxy(method, path, protocol, headers)
        except:
            len_local = len_remote = 0
        finally:
            writer.close()
        len_local += initial_len
        logger.info('%s %s X%s %.3fs <%d >%d',
                method.decode(), path,
                self.handler.socks_proxy or '-', time.time() - start_time, len_local, len_remote)

    async def open_connection(self, hostname, port):
        if self.handler.socks_proxy is None:
            logger.debug('request direct: %s:%s', hostname, port)
            self.remote = await asyncio.open_connection(hostname, port)
        logger.debug('request proxy: %s', self.handler.socks_proxy)
        client = create_client(self.handler.socks_proxy, remote_dns=True)
        await client.handle_connect((hostname, port))
        self.remote = client.reader, client.writer

    async def handle_connect(self, method, path, protocol, headers):
        hostinfo = Host(path)
        logger.debug('%s %s X%s', method.decode(), hostinfo.host, self.handler.socks_proxy or '-')
        await self.open_connection(hostinfo.hostname, hostinfo.port)
        await send_response(self.writer, protocol, message=b'Connection established')
        logger.debug('connection established')
        len_local, len_remote = await forward_pipes(self.reader, self.writer, *self.remote)
        return len_local, len_remote

    async def handle_proxy(self, method, path, protocol, headers):
        url = parse.urlparse(path)
        assert url.scheme == 'http'
        hostname = url.hostname
        port = url.port or 80
        pathname = url.path
        if url.query:
            pathname += '?' + url.query
        hostinfo = Host((hostname, port))
        logger.debug('%s %s X%s', method.decode(), hostinfo.host, self.handler.socks_proxy or '-')
        await self.open_connection(hostinfo.hostname, hostinfo.port)
        headers = [header for header in headers if not header[0].startswith(b'proxy-')]
        await send_request(self.remote[1], pathname.encode(), method, protocol, headers)
        logger.debug('send request: %s %s %s', pathname, method, headers)
        len_local, len_remote = await forward_pipes(self.reader, self.writer, *self.remote)
        return len_local, len_remote

class HTTPProxyHandler:
    def __init__(self, socks_proxy=None):
        self.socks_proxy = socks_proxy
        self.connections = set()

    async def __call__(self, reader, writer, feed=b''):
        request = HTTPProxyRequest(self, reader, writer)
        self.connections.add(request)
        try:
            await request.handle(feed)
        finally:
            self.connections.discard(request)

if __name__ == '__main__':
    from gera2ld.pyserve import start_server_asyncio, run_forever
    logging.basicConfig(level=logging.DEBUG)
    run_forever(start_server_asyncio(HTTPProxyHandler('socks5://localhost:2020'), ':2100'))
