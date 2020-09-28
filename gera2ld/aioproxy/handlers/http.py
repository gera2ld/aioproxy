import asyncio
import logging
import time
from urllib import parse
from gera2ld.pyserve import Host
from gera2ld.socks.client import create_client
from gera2ld.socks.utils import forward_pipes

async def read_headers(reader):
    while True:
        line = await reader.readline()
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

async def handle(reader, writer, socks_proxy=None, feed=b''):
    first_line = feed + await reader.readline()
    initial_len = len(first_line)
    method, path, protocol = first_line.strip().split(b' ', 3)
    headers = []
    async for line in read_headers(reader):
        initial_len += len(line)
        key, _, value = line.strip().partition(b':')
        if value is None: value = b''
        headers.append((key.strip().lower(), value.strip()))
    start_time = time.time()
    path = path.decode()
    try:
        if method == b'CONNECT':
            len_local, len_remote = await handle_connect(reader, writer, method, path, protocol, headers, socks_proxy)
        else:
            len_local, len_remote = await handle_proxy(reader, writer, method, path, protocol, headers, socks_proxy)
    except:
        len_local = len_remote = 0
        writer.close()
    proxy_log = ' X' + socks_proxy if socks_proxy else ''
    len_local += initial_len
    logging.info('%s %s%s %.3fs <%d >%d',
            method.decode(), path,
            proxy_log, time.time() - start_time, len_local, len_remote)

async def open_connection(hostname, port, socks_proxy):
    if socks_proxy is None:
        remote_reader, remote_writer = await asyncio.open_connection(hostname, port)
        return remote_reader, remote_writer
    client = create_client(socks_proxy, remote_dns=True)
    await client.handle_connect((hostname, port))
    return client.reader, client.writer

async def handle_connect(reader, writer, method, path, protocol, headers, socks_proxy):
    proxy_log = ' X' + socks_proxy if socks_proxy else ''
    hostinfo = Host(path)
    logging.debug('%s %s%s', method.decode(), hostinfo.host, proxy_log)
    await send_response(writer, protocol, message=b'Connection established')
    remote_reader, remote_writer = await open_connection(hostinfo.hostname, hostinfo.port, socks_proxy)
    len_local, len_remote, exc = await forward_pipes(reader, writer, remote_reader, remote_writer)
    return len_local, len_remote

async def handle_proxy(reader, writer, method, path, protocol, headers, socks_proxy):
    proxy_log = ' X' + socks_proxy if socks_proxy else ''
    url = parse.urlparse(path)
    assert url.scheme == 'http'
    hostname = url.hostname
    port = url.port or 80
    pathname = url.path
    if url.query:
        pathname += '?' + url.query
    hostinfo = Host((hostname, port))
    logging.debug('%s %s%s', method.decode(), hostinfo.host, proxy_log)
    remote_reader, remote_writer = await open_connection(hostinfo.hostname, hostinfo.port, socks_proxy)
    headers = [header for header in headers if not header[0].startswith(b'proxy-')]
    await send_request(remote_writer, pathname.encode(), method, protocol, headers)
    len_local, len_remote, exc = await forward_pipes(reader, writer, remote_reader, remote_writer)
    return len_local, len_remote

if __name__ == '__main__':
    from functools import partial
    from gera2ld.pyserve import start_server_asyncio, run_forever
    logging.basicConfig(level=logging.INFO)
    run_forever(start_server_asyncio(partial(handle, socks_proxy='socks5://127.0.0.1:2020'), ':2100'))
