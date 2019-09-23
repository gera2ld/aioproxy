import sys
import platform
import urllib
import logging
import asyncio
import click
from gera2ld.pyserve import get_url_items, print_urls, run_forever
from aiohttp import web
from aiohttp.log import server_logger
from . import __version__
from .handlers import handle

def parse_addr(host, default=('', 80)):
    result = urllib.parse.urlparse('//' + host)
    hostname = result.hostname
    if hostname is None: hostname = default[0]
    port = result.port
    if port is None: port = default[0]
    return hostname, port

async def create_server(host, port):
    web_server = web.Server(handle)
    runner = web.ServerRunner(web_server)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner

@click.command()
@click.option('-b', '--bind', default=':5000', help='the address to bind, default as `:5000`')
def main(bind):
    logging.basicConfig(level=logging.INFO)
    host, port = parse_addr(bind)
    server_logger.info(
        'Proxy Server v%s/%s %s - by Gerald',
        __version__, platform.python_implementation(), platform.python_version())
    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(create_server(host, port))
    print_urls([get_url_items(runner.addresses)])
    run_forever(loop)
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
