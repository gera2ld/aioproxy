import sys
import logging
import asyncio
from aiohttp import web
from .handler import handle

def main():
    logging.basicConfig(level=logging.INFO)
    kw = { 'access_log': None }

    server = web.Server(handle)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_server(server, '0.0.0.0', 8080))
    loop.run_forever()

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
