import sys
import platform
import urllib
import logging
import asyncio
import click
from gera2ld.pyserve import serve_aiohttp
from aiohttp import web
from aiohttp.log import server_logger
from . import __version__
from .handlers import handle

@click.command()
@click.option('-b', '--bind', default=':5000', help='the address to bind, default as `:5000`')
def main(bind):
    logging.basicConfig(level=logging.INFO)
    server_logger.info(
        'Proxy Server v%s/%s %s - by Gerald',
        __version__, platform.python_implementation(), platform.python_version())
    serve_aiohttp(handle, bind)
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
