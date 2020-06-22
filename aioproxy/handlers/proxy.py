import asyncio
import aiohttp
import socket
from typing import Any, Dict, List, Optional
from aiohttp import web, TCPConnector
from aiohttp.abc import AbstractResolver
from aiohttp.helpers import get_running_loop
from async_dns import types
from .util import forward_data
from .dns import get_resolver

resolver = None

class AsyncResolver(AbstractResolver):
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
        self._loop = get_running_loop(loop)
        self._resolver = get_resolver()

    async def resolve(self, host: str, port: int=0,
                      family: int=socket.AF_INET) -> List[Dict[str, Any]]:
        if family == socket.AF_INET:
            qtype = types.A
        elif family == socket.AF_INET6:
            qtype = types.AAAA
        else:
            qtype = types.ANY
        res = await self._resolver.query(host, qtype)
        hosts = []
        if res:
            for item in res.an:
                if item.qtype in (types.A, types.AAAA):
                    hosts.append({
                        'hostname': host,
                        'host': item.data,
                        'port': port,
                        'family': socket.AF_INET if item.qtype == types.A else socket.AF_INET6,
                        'proto': 0,
                        'flags': socket.AI_NUMERICHOST,
                    })
        return hosts

    async def close(self) -> None:
        pass

async def handle(request):
    global resolver
    if resolver is None:
        resolver = AsyncResolver()
    connector = TCPConnector(force_close=True, resolver=resolver)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.request(
            request.method,
            request.raw_path,
            headers=request.headers,
            data=await request.content.read(),
            allow_redirects=False,
        ) as client_response:
            headers = client_response.headers.copy()
            headers.popall('content-length', None)
            headers.popall('content-encoding', None)
            headers.popall('transfer-encoding', None)
            headers.popall('etag', None)
            for key in headers.keys():
                if key.lower().startswith('proxy-'):
                    headers.popall(key, None)
            response = web.StreamResponse(
                status=client_response.status,
                reason=client_response.reason,
                headers=headers,
            )
            await response.prepare(request)
            await forward_data(client_response.content, response)
            return response
