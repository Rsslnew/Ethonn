# ethon/telefunc.py — FINAL FIXED VERSION

import os
import time

from .FasterTg import download_file
from telethon.errors.rpcerrorlist import UserNotParticipantError, MessageNotModifiedError
from telethon.tl.functions.channels import GetParticipantRequest
from main.plugins.userqueue import RUNNING_TASK


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


# ───────────────────────── PROGRESS ─────────────────────────

_last_edit = {}

async def progress(current, total, event, start, type_of_ps, file=None):
    now = time.time()
    diff = now - start

    if diff <= 0:
        return

    key = id(event)

    # throttle biar gak spam edit
    if key in _last_edit and now - _last_edit[key] < 0.5:
        return

    _last_edit[key] = now

    try:
        percentage = (current * 100 / total) if total else 0
        percentage = min(100, percentage)

        speed = current / diff if diff > 0 else 0
        if speed <= 0:
            speed = 1

        eta = (total - current) / speed if speed > 0 else 0

        filled = int(percentage // 5)
        bar = "█" * filled + "░" * (20 - filled)

        frames = ["▱▱▱▱▱", "▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]
        frame = frames[int(time.time() * 2) % len(frames)]

        text = (
            f"{type_of_ps}\n\n"
            f"{frame} **{percentage:.2f}%**\n"
            f"{bar}\n\n"
            f"📦 `{hbs(current)} / {hbs(total)}`\n"
            f"🚀 `{hbs(speed)}/s`\n"
            f"⏱️ `{time_formatter(int(eta * 1000))}`"
        )

        if file:
            text += f"\n\n📄 `{file}`"

        await event.edit(text)

    except MessageNotModifiedError:
        pass
    except:
        pass


# ───────────────────────── MEDIA FIX ─────────────────────────

def _get_safe_media(file):
    try:
        if hasattr(file, "document") and file.document:
            return file.document
    except:
        pass
    return file


# ───────────────────────── FAST DOWNLOAD ─────────────────────────

async def fast_download(filename, file, bot, event, start_time, msg, user_id=None):

    file = _get_safe_media(file)

    with open(filename, "wb") as fk:
        result = await download_file(
            client=bot,
            location=file,
            out=fk,
            progress_callback=lambda d, t: progress(
                d, t, event, start_time, msg, filename
            ),
            user_id=user_id
        )

    _last_edit.pop(id(event), None)

    return result


# ───────────────────────── FAST UPLOAD (FIX PALING PENTING) ─────────────────────────

async def fast_upload(file, name, start_time, bot, event, msg, user_id=None):

    size = os.path.getsize(file)

    with open(file, "rb") as f:
        result = await bot.upload_file(
            f,
            file_name=name,
            file_size=size,
            progress_callback=lambda d, t: progress(
                d, t, event, start_time, msg, name
            )
        )

    _last_edit.pop(id(event), None)

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

    except:
        s, r = True, "ERROR: ForceSub config invalid."

    return s, r