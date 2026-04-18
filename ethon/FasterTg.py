# FASTERTG FIXED (cancel support + safer loop)
#credit @K6991

import asyncio
import hashlib
import logging
import math
import os
from collections import defaultdict
from typing import (
    AsyncGenerator,
    Awaitable,
    BinaryIO,
    DefaultDict,
    List,
    Optional,
    Tuple,
    Union,
)

from telethon import TelegramClient, helpers, utils
from telethon.crypto import AuthKey
from telethon.helpers import _maybe_await
from telethon.network import MTProtoSender
from telethon.tl.alltlobjects import LAYER
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.functions.auth import (
    ExportAuthorizationRequest,
    ImportAuthorizationRequest,
)
from telethon.tl.functions.upload import (
    GetFileRequest,
    SaveBigFilePartRequest,
    SaveFilePartRequest,
)
from telethon.tl.types import (
    Document,
    InputDocumentFileLocation,
    InputFile,
    InputFileBig,
    InputFileLocation,
    InputPeerPhotoFileLocation,
    InputPhotoFileLocation,
    TypeInputFile,
)

# ✅ IMPORT RUNNING (WAJIB)
from main.plugins.userqueue import RUNNING

log: logging.Logger = logging.getLogger("FasterTg")

TypeLocation = Union[
    Document,
    InputDocumentFileLocation,
    InputPeerPhotoFileLocation,
    InputFileLocation,
    InputPhotoFileLocation,
]


# ───────────────────────── DOWNLOAD SENDER ─────────────────────────

class DownloadSender:
    def __init__(self, client, sender, file, offset, limit, stride, count):
        self.sender = sender
        self.client = client
        self.request = GetFileRequest(file, offset=offset, limit=limit)
        self.stride = stride
        self.remaining = count

    async def next(self):
        if not self.remaining:
            return None
        result = await self.client._call(self.sender, self.request)
        self.remaining -= 1
        self.request.offset += self.stride
        return result.bytes

    def disconnect(self):
        return self.sender.disconnect()


# ───────────────────────── UPLOAD SENDER ─────────────────────────

class UploadSender:
    def __init__(self, client, sender, file_id, part_count, big, index, stride, loop):
        self.client = client
        self.sender = sender
        self.part_count = part_count
        if big:
            self.request = SaveBigFilePartRequest(file_id, index, part_count, b"")
        else:
            self.request = SaveFilePartRequest(file_id, index, b"")
        self.stride = stride
        self.previous = None
        self.loop = loop

    async def next(self, data):
        if self.previous:
            await self.previous
        self.previous = self.loop.create_task(self._next(data))

    async def _next(self, data):
        self.request.bytes = data
        await self.client._call(self.sender, self.request)
        self.request.file_part += self.stride

    async def disconnect(self):
        if self.previous:
            await self.previous
        return await self.sender.disconnect()


# ───────────────────────── MAIN TRANSFER ─────────────────────────

class ParallelTransferrer:
    def __init__(self, client, dc_id=None):
        self.client = client
        self.loop = client.loop
        self.dc_id = dc_id or client.session.dc_id
        self.auth_key = client.session.auth_key
        self.senders = None
        self.upload_ticker = 0

    async def _cleanup(self):
        if self.senders:
            await asyncio.gather(*[s.disconnect() for s in self.senders], return_exceptions=True)
        self.senders = None

    @staticmethod
    def _get_connection_count(file_size):
        if file_size > 100 * (1024**2):
            return 20
        return max(1, math.ceil((file_size / (100 * (1024**2))) * 20))

    async def _create_sender(self):
        dc = await self.client._get_dc(self.dc_id)
        sender = MTProtoSender(self.auth_key, loggers=self.client._log)

        await sender.connect(
            self.client._connection(
                dc.ip_address,
                dc.port,
                dc.id,
                loggers=self.client._log,
                proxy=self.client._proxy,
            )
        )
        return sender

    async def _init_download(self, connections, file, part_count, part_size):
        self.senders = [
            await self._create_download_sender(file, i, part_size, connections * part_size, part_count // connections)
            for i in range(connections)
        ]

    async def _create_download_sender(self, file, index, part_size, stride, count):
        return DownloadSender(
            self.client,
            await self._create_sender(),
            file,
            index * part_size,
            part_size,
            stride,
            count,
        )

    async def download(self, file, file_size, user_id=None):
        connections = self._get_connection_count(file_size)
        part_size = utils.get_appropriated_part_size(file_size) * 1024
        part_count = math.ceil(file_size / part_size)

        await self._init_download(connections, file, part_count, part_size)

        part = 0

        try:
            while part < part_count:

                # ❌ CANCEL CHECK
                if user_id and user_id not in RUNNING:
                    break

                tasks = [self.loop.create_task(s.next()) for s in self.senders]

                for task in tasks:
                    data = await task
                    if not data:
                        break

                    yield data
                    part += 1

        finally:
            await self._cleanup()

    async def upload(self, part, user_id=None):

        # ❌ CANCEL CHECK
        if user_id and user_id not in RUNNING:
            return

        await self.senders[self.upload_ticker].next(part)
        self.upload_ticker = (self.upload_ticker + 1) % len(self.senders)

    async def finish_upload(self):
        await self._cleanup()


# ───────────────────────── API ─────────────────────────

async def download_file(client, location, out, progress_callback=None, user_id=None):
    size = location.size
    dc_id, location = utils.get_input_location(location)

    downloader = ParallelTransferrer(client, dc_id)

    async for x in downloader.download(location, size, user_id=user_id):

        if user_id and user_id not in RUNNING:
            break

        out.write(x)

        if progress_callback:
            try:
                await _maybe_await(progress_callback(out.tell(), size))
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    return out


async def upload_file(client, file, filename, progress_callback=None, user_id=None):

    file_id = helpers.generate_random_long()
    file_size = os.path.getsize(file.name)

    uploader = ParallelTransferrer(client)

    part_size = utils.get_appropriated_part_size(file_size) * 1024
    part_count = math.ceil(file_size / part_size)

    uploader.senders = [
    UploadSender(
        client,
        await uploader._create_sender(),
        file_id,
        part_count,
        file_size > 10 * 1024 * 1024,
        i,
        4,
        client.loop
    )
    for i in range(4)
]

    for chunk in iter(lambda: file.read(part_size), b""):

        if user_id and user_id not in RUNNING:
            break

        await uploader.upload(chunk, user_id=user_id)

        if progress_callback:
            try:
                await _maybe_await(progress_callback(file.tell(), file_size))
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    await uploader.finish_upload()

    return InputFileBig(file_id, part_count, filename)