BUF_SIZE = 4096

async def forward_data(reader, writer):
    while True:
        try:
            chunk = await reader.read(BUF_SIZE)
        except ConnectionResetError:
            break
        if not chunk:
            break
        await writer.write(chunk)
