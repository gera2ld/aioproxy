import asyncio
import aiohttp
import socket
from typing import Any, Dict, List, Optional, Tuple, Type
from aiohttp import web, TCPConnector
from aiohttp.helpers import get_running_loop
from aiohttp.client_proto import ResponseHandler
from gera2ld.socks.client import create_client
from .util import forward_data

class SOCKSConnector(TCPConnector):
    def __init__(self, socks_proxy, *k, **kw):
        super().__init__(*k, **kw)
        self.socks_proxy = socks_proxy

    async def _create_connection(self, req: 'ClientRequest',
                                 traces: List['Trace'],
                                 timeout: 'ClientTimeout') -> ResponseHandler:
        client = create_client(self.socks_proxy, remote_dns=True)
        await client.handle_connect((req.url.host, req.url.port))
        rawsock = client.writer._transport.get_extra_info('socket', default=None)
        _transp, proto = await self._wrap_create_connection(
            self._factory, timeout=timeout,
            sock=rawsock,
            req=req)
        return proto

async def handle(handler, request):
    connector = SOCKSConnector(handler.socks_proxy, force_close=True)
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
