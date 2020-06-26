import os
import sys
import platform
import logging
import click
from gera2ld.pyserve import run_forever, start_server_aiohttp
from aiohttp.log import server_logger
from . import __version__
from .handlers import Handler

@click.command()
@click.option('-b', '--bind', default=':1086', help='the server address to bind')
@click.option('-x', '--proxy', default='socks5://127.0.0.1:1080', help='downstream SOCKS proxy')
def main(bind, proxy):
    logging.basicConfig(level=logging.INFO)
    server_logger.info(
        'Proxy Server v%s/%s %s - by Gerald',
        __version__, platform.python_implementation(), platform.python_version())
    run_forever(start_server_aiohttp(Handler(proxy), bind))
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
