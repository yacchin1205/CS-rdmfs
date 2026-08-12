import pytest
from mock import AsyncMock, MagicMock

from rdmfs.upload import create_file, update_file


def response(status_code):
    value = MagicMock()
    value.status_code = status_code
    return value


@pytest.mark.asyncio
async def test_create_file_streams_with_content_length():
    storage = MagicMock()
    folder = MagicMock()
    folder._new_file_url = 'https://files.test/folder/?kind=file'
    folder._put = AsyncMock(return_value=response(201))
    storage.create_folder = AsyncMock(return_value=folder)
    fp = MagicMock()

    await create_file(storage, '/folder/file.txt', fp, 7)

    storage.create_folder.assert_awaited_once_with('folder', exist_ok=True)
    _, kwargs = folder._put.call_args
    assert kwargs['params'] == {'kind': 'file', 'name': 'file.txt'}
    assert kwargs['headers'] == {'Content-Length': '7'}
    assert hasattr(kwargs['content'], '__aiter__')


@pytest.mark.asyncio
async def test_create_empty_file_sends_zero_content_length():
    storage = MagicMock()
    storage._new_file_url = 'https://files.test/?kind=file'
    storage._put = AsyncMock(return_value=response(201))

    await create_file(storage, '/empty.txt', MagicMock(), 0)

    _, kwargs = storage._put.call_args
    assert kwargs['headers'] == {'Content-Length': '0'}
    assert kwargs['content'] == b''


@pytest.mark.asyncio
async def test_create_file_reports_waterbutler_error():
    storage = MagicMock()
    storage._new_file_url = 'https://files.test/?kind=file'
    storage._put = AsyncMock(return_value=response(411))

    with pytest.raises(RuntimeError, match='status code: 411'):
        await create_file(storage, '/file.txt', MagicMock(), 7)


@pytest.mark.asyncio
async def test_update_file_streams_with_content_length():
    file_ = MagicMock()
    file_.path = '/file.txt'
    file_._upload_url = 'https://files.test/file-id'
    file_._put = AsyncMock(return_value=response(200))

    await update_file(file_, MagicMock(), 7)

    _, kwargs = file_._put.call_args
    assert kwargs['headers'] == {'Content-Length': '7'}
    assert hasattr(kwargs['content'], '__aiter__')


@pytest.mark.asyncio
async def test_update_file_reports_waterbutler_error():
    file_ = MagicMock()
    file_.path = '/file.txt'
    file_._upload_url = 'https://files.test/file-id'
    file_._put = AsyncMock(return_value=response(411))

    with pytest.raises(RuntimeError, match='status code: 411'):
        await update_file(file_, MagicMock(), 7)
