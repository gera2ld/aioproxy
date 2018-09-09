import asyncio
import aiohttp
from aiohttp import web, streams

BUF_SIZE = 4096

async def forward_data(reader, writer):
    while True:
        chunk = await reader.read(BUF_SIZE)
        if not chunk:
            break
        await writer.write(chunk)

class ConnectReader:
    def __init__(self, queue):
        self.queue = queue
        self._exc = None

    def feed_eof(self):
        self.queue.feed_eof()

    def feed_data(self, data):
        if self._exc:
            return True, data
        try:
            self.queue.feed_data(data, len(data))
            return False, b''
        except Exception as exc:
            self._exc = exc
            self.queue.set_exception(exc)
            return True, b''

async def handle_connect(request):
    host, _, port = request.raw_path.partition(':')
    port = int(port)
    reader, writer = await asyncio.open_connection(host, port, loop=request._loop)
    response = web.StreamResponse(
        status=200,
        reason='Connection established',
    )
    await response.prepare(request)
    response._reader = streams.DataQueue(loop=request._loop)
    request.protocol.set_parser(ConnectReader(response._reader))
    request.protocol.keep_alive(False)
    async def forward_client_data():
        async for chunk in response._reader:
            writer.write(chunk)
            await writer.drain()
        reader.feed_eof()
    try:
        await asyncio.wait([
            forward_client_data(),
            forward_data(reader, response),
        ])
    except asyncio.CancelledError:
        # Connection lost causes cancellation of current task,
        # we catch CancelledError so that access will still be logged.
        pass
    return response

async def handle_request(request):
    async with aiohttp.ClientSession() as session:
        async with session.request(
            request.method,
            request.raw_path,
            headers=request.headers,
            allow_redirects=False,
        ) as client_response:
            headers = client_response.headers.copy()
            headers.popall('content-encoding', None)
            headers.popall('transfer-encoding', None)
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

async def handle(request):
    if request.method == 'CONNECT':
        return await handle_connect(request)
    return await handle_request(request)
