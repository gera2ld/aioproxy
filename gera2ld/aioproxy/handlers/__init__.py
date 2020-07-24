from .http import handle as handle_http

async def handle(reader, writer, socks_proxy=None):
    await handle_http(reader, writer, socks_proxy)
