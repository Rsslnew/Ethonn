#idk

import math
import time
import asyncio

from .FasterTg import upload_file, download_file

from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest


# ───────────────────────── UTIL ─────────────────────────

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)

    tmp = (
        ((str(weeks) + "w:") if weeks else "")
        + ((str(days) + "d:") if days else "")
        + ((str(hours) + "h:") if hours else "")
        + ((str(minutes) + "m:") if minutes else "")
        + ((str(seconds) + "s") if seconds else "")
    )
    return tmp or "0s"


def hbs(size):
    if not size:
        return "0 B"

    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}

    while size > power and raised_to_pow < 4:
        size /= power
        raised_to_pow += 1

    return f"{round(size, 2)} {dict_power_n[raised_to_pow]}"


# ───────────────────────── PROGRESS (FIXED) ─────────────────────────

_last_edit = {}  # anti spam per message


async def progress(current, total, event, start, type_of_ps, file=None):
    now = time.time()
    diff = now - start

    if diff == 0:
        return

    # throttle update tiap ~2 detik
    key = id(event)
    if key in _last_edit and now - _last_edit[key] < 2:
        return

    _last_edit[key] = now

    try:
        percentage = current * 100 / total
        speed = current / diff
        eta = (total - current) / speed if speed > 0 else 0

        filled = int(percentage // 5)
        bar = "🟩" * filled + "⬜️" * (20 - filled)

        text = (
            f"{type_of_ps}\n\n"
            f"**[{bar}] {percentage:.2f}%**\n\n"
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
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, event, start_time, msg, name)
            ),
        )
    return result


async def fast_download(filename, file, bot, event, start_time, msg):
    with open(filename, "wb") as fk:
        result = await download_file(
            client=bot,
            location=file,
            out=fk,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, event, start_time, msg, filename)
            ),
        )
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