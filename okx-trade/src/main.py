import asyncio
import aiodemo


async def main():
    async_tasks = [
        # asyncio.create_task(aiodemo.simple()),
        asyncio.create_task(aiodemo.daemon(10)),
        asyncio.create_task(aiodemo.instance()),
    ]
    await asyncio.wait(async_tasks)


if __name__ == '__main__':
    asyncio.run(main())
