import asyncio
import logging
from pathlib import Path

import aiofiles
import aiohttp
from src.constants import CHUNK_SIZE, CONCURRENCY, DOWNLOAD_PATH, LOGGING_LEVEL
from tqdm import tqdm

logging.basicConfig(level=LOGGING_LEVEL)


class FileLoader:
    """Скачивает файлы асинхронно по списку url

    cookie - словарь с кукис, который надо использовать в сессии,
    load_list - список URL файлов для скачивания,
    download_path - путь для скачивания, по умолчанию ./download
    """

    load_path: Path = None
    load_list: list = []
    cookie: dict
    chunk_size = CHUNK_SIZE
    concurrent_count = CONCURRENCY  # одновременно будет скачиваться файлов

    def __init__(self, cookie: dict[str, str], load_list: list[str], download_path: Path = None):
        self.load_path = download_path or DOWNLOAD_PATH
        self.load_list = load_list
        self.cookie = cookie
        if not self.load_path.exists():
            self.load_path.mkdir()

    async def start(self) -> tuple[bool | Exception]:
        """Запуск скачивания.
        Возвращает кортеж из True - если скачали и исключение, если что-то пошло не так"""

        semaphore = asyncio.Semaphore(self.concurrent_count)

        async def download_file(url: str):
            filename = url.split("/")[-1]
            async with semaphore:
                async with aiofiles.open(self.load_path / filename, "wb") as f:
                    async with aiohttp.ClientSession(cookies=self.cookie) as session:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            total = int(response.headers.get("content-length", 0))

                            tqdm_params = {
                                "desc": url,
                                "total": total,
                                "miniters": 1,
                                "unit": "it",
                                "unit_scale": True,
                                "unit_divisor": 1024,
                            }
                            with tqdm(**tqdm_params) as pb:
                                async for chunk in response.content.iter_chunked(self.chunk_size):
                                    pb.update(len(chunk))
                                    await f.write(chunk)
            return True

        tasks = [asyncio.create_task(download_file(url)) for url in self.load_list]
        return await asyncio.gather(*tasks, return_exceptions=True)
