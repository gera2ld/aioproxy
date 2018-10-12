import aiohttp
from aiohttp import web
from .util import forward_data

async def handle(request):
    async with aiohttp.ClientSession() as session:
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
