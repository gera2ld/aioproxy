import asyncio

BUF_SIZE = 4096

async def forward_data(reader, writer, count):
    while True:
        data = await reader.read(BUF_SIZE)
        if not data: break
        writer.write(data)
        count(len(data))
        await writer.drain()

class Counter:
    def __init__(self):
        self.value = 0

    def count(self, size):
        self.value += size

async def forward_pipes(reader, writer, remote_reader, remote_writer):
    local_counter = Counter()
    remote_counter = Counter()
    _done, pending = await asyncio.wait(
        [
            forward_data(reader, remote_writer, local_counter.count),
            forward_data(remote_reader, writer, remote_counter.count),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    return local_counter.value, remote_counter.value
