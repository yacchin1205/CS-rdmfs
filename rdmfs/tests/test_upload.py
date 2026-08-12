from types import SimpleNamespace

import httpx
import pytest
from mock import AsyncMock

from rdmfs.upload import create_file, update_file


class AsyncContent:
    def __init__(self, *chunks):
        self.chunks = chunks
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index == len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


def response(status_code):
    return SimpleNamespace(status_code=status_code)


@pytest.mark.asyncio
async def test_create_file_streams_with_content_length():
    folder = SimpleNamespace(
        _new_file_url='https://files.test/folder/?kind=file',
        _put=AsyncMock(return_value=response(201)),
    )
    storage = SimpleNamespace(
        create_folder=AsyncMock(return_value=folder),
    )
    content = AsyncContent(b'content')

    await create_file(storage, '/folder/file.txt', content, 7)

    storage.create_folder.assert_awaited_once_with('folder', exist_ok=True)
    _, kwargs = folder._put.call_args
    assert kwargs['params'] == {'kind': 'file', 'name': 'file.txt'}
    assert kwargs['headers'] == {'Content-Length': '7'}
    assert kwargs['content'] is content


@pytest.mark.asyncio
async def test_create_empty_file_sends_zero_content_length():
    storage = SimpleNamespace(
        _new_file_url='https://files.test/?kind=file',
        _put=AsyncMock(return_value=response(201)),
    )
    content = AsyncContent()

    await create_file(storage, '/empty.txt', content, 0)

    _, kwargs = storage._put.call_args
    assert kwargs['headers'] == {'Content-Length': '0'}
    assert kwargs['content'] is content


@pytest.mark.asyncio
async def test_create_file_reports_waterbutler_error():
    storage = SimpleNamespace(
        _new_file_url='https://files.test/?kind=file',
        _put=AsyncMock(return_value=response(411)),
    )

    with pytest.raises(RuntimeError, match='status code: 411'):
        await create_file(storage, '/file.txt', AsyncContent(b'content'), 7)


@pytest.mark.asyncio
async def test_create_file_http_request_is_not_chunked():
    async def handle(request):
        assert request.headers['Content-Length'] == '7'
        assert 'Transfer-Encoding' not in request.headers
        assert await request.aread() == b'content'
        return httpx.Response(201)

    transport = httpx.MockTransport(handle)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SimpleNamespace(
            _new_file_url='https://files.test/?kind=file',
            _put=client.put,
        )
        await create_file(
            storage, '/file.txt', AsyncContent(b'content'), 7
        )


@pytest.mark.asyncio
async def test_update_file_streams_with_content_length():
    file_ = SimpleNamespace(
        path='/file.txt',
        _upload_url='https://files.test/file-id',
        _put=AsyncMock(return_value=response(200)),
    )
    content = AsyncContent(b'content')

    await update_file(file_, content, 7)

    _, kwargs = file_._put.call_args
    assert kwargs['headers'] == {'Content-Length': '7'}
    assert kwargs['content'] is content


@pytest.mark.asyncio
async def test_update_file_reports_waterbutler_error():
    file_ = SimpleNamespace(
        path='/file.txt',
        _upload_url='https://files.test/file-id',
        _put=AsyncMock(return_value=response(411)),
    )

    with pytest.raises(RuntimeError, match='status code: 411'):
        await update_file(file_, AsyncContent(b'content'), 7)
