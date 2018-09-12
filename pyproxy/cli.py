import sys
import platform
import urllib
import logging
import asyncio
import click
from aiohttp import web
from aiohttp.log import server_logger, access_logger
from . import __version__
from .handler import handle

def parse_addr(host, default=('', 80)):
    result = urllib.parse.urlparse('//' + host)
    hostname = result.hostname
    if hostname is None: hostname = default[0]
    port = result.port
    if port is None: port = default[0]
    return hostname, port

@click.command()
@click.option('-b', '--bind', default=':5000', help='the address to bind, default as `:5000`')
def main(bind):
    logging.basicConfig(level=logging.INFO)
    host, port = parse_addr(bind)
    server_logger.info(
        'Proxy Server v%s/%s %s - by Gerald',
        __version__, platform.python_implementation(), platform.python_version())
    server = web.Server(handle)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_server(server, host, port))
    loop.run_forever()
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
