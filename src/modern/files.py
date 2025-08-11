from pathlib import Path

from fastapi import UploadFile

import aiofiles as aiof

UPLOAD_DIR = Path("/tmp")
BUFFER_SIZE = 1024 * 1024


async def add_file(name: str, stream: UploadFile) -> str:
    """
    Add the byte stream as the file with name 'name' into self.
    :param name: File name.
    :param stream: The byte stream with file content.
    """
    dest_path = UPLOAD_DIR.joinpath(name)

    # Copy data from the stream into dest_path
    async with aiof.open(dest_path, "wb") as fout:
        buff = await stream.read(BUFFER_SIZE)
        while len(buff) != 0:
            await fout.write(buff)
            buff = await stream.read(BUFFER_SIZE)
    return str(dest_path)
