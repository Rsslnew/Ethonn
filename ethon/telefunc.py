#idk

import math
import time
import asyncio

from .FasterTg import upload_file, download_file
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from main.plugins.userqueue import RUNNING


# ───────────────────────── UTIL ─────────────────────────

def time_formatter(milliseconds: int) -> str:
    seconds, _ = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def hbs(size):
    if not size:
        return "0 B"

    power = 1024
    units = ["B", "KB", "MB", "GB", "TB"]

    i = 0
    size = float(size)

    while size >= power and i < len(units) - 1:
        size /= power
        i += 1

    return f"{size:.2f} {units[i]}"


# ───────────────────────── PROGRESS (FINAL) ─────────────────────────

_last_edit = {}


async def progress(current, total, event, start, type_of_ps, file=None):
    now = time.time()
    diff = now - start

    if diff <= 0:
        return

    # pakai message id biar stabil
    key = getattr(event, "id", id(event))

    # throttle 2 detik
    if key in _last_edit and now - _last_edit[key] < 2:
        return

    _last_edit[key] = now

    try:
        # CANCEL CHECK
        user_id = getattr(event, "sender_id", None)
        if user_id and user_id not in RUNNING:
            return

        percentage = (current * 100 / total) if total else 0
        speed = current / diff if diff else 0

        eta = (total - current) / speed if speed > 0 else 0

        filled = int(percentage // 5)
        bar = "🟩" * filled + "⬜️" * (20 - filled)

        text = (
            f"{type_of_ps}\n\n"
            f"**{percentage:.2f}%**\n"
            f"[{bar}]\n\n"
            f"📦 {hbs(current)} / {hbs(total)}\n"
            f"🚀 {hbs(speed)}/s\n"
            f"⏱️ ETA: {time_formatter(int(eta * 1000))}"
        )

        if file:
            text += f"\n\n📄 `{file}`"

        await event.edit(text)

    except Exception:
        pass


# ───────────────────────── FAST UPLOAD/DOWNLOAD ─────────────────────────

async def fast_upload(file, name, start_time, bot, event, msg):
    with open(file, "rb") as f:
        result = await upload_file(
            client=bot,
            file=f,
            filename=name,
            progress_callback=lambda d, t: asyncio.create_task(
                progress(d, t, event, start_time, msg, name)
            ),
        )

    # cleanup memory
    _last_edit.pop(getattr(event, "id", id(event)), None)

    return result


async def fast_download(filename, file, bot, event, start_time, msg):
    with open(filename, "wb") as fk:
        result = await download_file(
            client=bot,
            location=file,
            out=fk,
            progress_callback=lambda d, t: asyncio.create_task(
                progress(d, t, event, start_time, msg, filename)
            ),
        )

    # cleanup memory
    _last_edit.pop(getattr(event, "id", id(event)), None)

    return result


# ───────────────────────── FORCE SUB ─────────────────────────

async def force_sub(client, channel, id, ft):
    s, r = False, None

    try:
        x = await client(GetParticipantRequest(channel=channel, participant=int(id)))
        left = x.stringify()

        if "left" in left:
            s, r = True, f"{ft}\n\nAlso join @{channel}"
        else:
            s, r = False, None

    except UserNotParticipantError:
        s, r = True, f"To use this bot you've to join @{channel}"

    except Exception:
        s, r = True, "ERROR: ForceSub config invalid."

    return s, r