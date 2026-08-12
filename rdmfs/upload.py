import os
from collections.abc import AsyncIterable

from osfclient.models.utils import merge_query_params
from osfclient.utils import norm_remote_path


async def create_file(
    storage, path, content: AsyncIterable[bytes], size: int
):
    path = norm_remote_path(path)
    directory, filename = os.path.split(path)

    parent = storage
    for part in directory.split(os.path.sep):
        if part:
            parent = await parent.create_folder(part, exist_ok=True)

    url = parent._new_file_url
    response = await parent._put(
        url,
        params=merge_query_params(url, {'name': filename}),
        headers={'Content-Length': str(size)},
        content=content,
    )
    if response.status_code == 409:
        raise FileExistsError(path)
    if response.status_code != 201:
        raise RuntimeError(
            'Could not create {} (status code: {}).'.format(
                path, response.status_code
            )
        )


async def update_file(file_, content: AsyncIterable[bytes], size: int):
    response = await file_._put(
        file_._upload_url,
        headers={'Content-Length': str(size)},
        content=content,
    )
    if response.status_code != 200:
        raise RuntimeError(
            'Could not update {} (status code: {}).'.format(
                file_.path, response.status_code
            )
        )
