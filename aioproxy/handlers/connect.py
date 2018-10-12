from aiohttp import web, streams

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

async def handle(request):
    host, _, port = request.raw_path.partition(':')
    port = int(port)
    reader, writer = await asyncio.open_connection(host, port, loop=request._loop)
    response = web.StreamResponse(
        status=200,
        reason='Connection established',
    )
    # disable chunked encoding
    response._length_check = False
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
