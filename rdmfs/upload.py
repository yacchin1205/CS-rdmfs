import os

from osfclient.models.utils import chunked_bytes_iterator, merge_query_params
from osfclient.utils import norm_remote_path


def _content(fp, size):
    if size == 0:
        return b''
    return chunked_bytes_iterator(fp)


def _headers(size):
    # HTTPX otherwise sends an AsyncIterable with Transfer-Encoding: chunked,
    # while WaterButler requires Content-Length for file uploads.
    return {'Content-Length': str(size)}


async def create_file(storage, path, fp, size):
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
        headers=_headers(size),
        content=_content(fp, size),
    )
    if response.status_code == 409:
        raise FileExistsError(path)
    if response.status_code != 201:
        raise RuntimeError(
            'Could not create {} (status code: {}).'.format(
                path, response.status_code
            )
        )


async def update_file(file_, fp, size):
    response = await file_._put(
        file_._upload_url,
        headers=_headers(size),
        content=_content(fp, size),
    )
    if response.status_code != 200:
        raise RuntimeError(
            'Could not update {} (status code: {}).'.format(
                file_.path, response.status_code
            )
        )
