import asyncio

import aiohttp


async def main():
    client = aiohttp.ClientSession()

    response = await client.delete(
        "http://127.0.0.1:8080/ad/1"
    )
    print(response.status)
    print(await response.text())

    await client.close()


asyncio.run(main())
