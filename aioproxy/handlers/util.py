import asyncio

BUF_SIZE = 4096

async def forward_data(reader, writer):
    try:
        while True:
            try:
                chunk = await reader.read(BUF_SIZE)
            except ConnectionResetError:
                break
            if not chunk:
                break
            # https://github.com/aio-libs/aiohttp/issues/3122#issuecomment-567960647
            await asyncio.shield(writer.write(chunk))
    finally:
        await writer.write_eof()
