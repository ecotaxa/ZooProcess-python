from pathlib import Path

from fastapi import UploadFile

UPLOAD_DIR = Path("/tmp")


async def add_file(name: str, stream: UploadFile) -> str:
    """
    Add the byte stream as the file with name 'name' into self.
    :param name: File name.
    :param stream: The byte stream with file content.
    """
    dest_path = UPLOAD_DIR.joinpath(name)

    # Copy data from the stream into dest_path
    with open(dest_path, "wb") as fout:
        buff = await stream.read(1024)
        while len(buff) != 0:
            fout.write(buff)  # type:ignore # Mypy is unaware of async read result
            buff = await stream.read(1024)
    return str(dest_path)
