BUF_SIZE = 4096

async def forward_data(reader, writer):
    while True:
        chunk = await reader.read(BUF_SIZE)
        if not chunk:
            break
        await writer.write(chunk)
