import os
import sys
import platform
import logging
import click
from gera2ld.pyserve import run_forever, start_server_asyncio
from . import __version__
from .handlers import create_handler

@click.command()
@click.option('-b', '--bind', default=':2020', help='the server address to bind')
@click.option('-x', '--proxy', default='socks5://127.0.0.1:1080', help='downstream SOCKS proxy, `none` for direct connection')
def main(bind, proxy):
    logging.basicConfig(level=logging.INFO)
    logging.info(
        'Proxy Server v%s/%s %s - by Gerald',
        __version__, platform.python_implementation(), platform.python_version())
    if proxy == 'none': proxy = None
    run_forever(start_server_asyncio(create_handler(socks_proxy=proxy), bind))
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
