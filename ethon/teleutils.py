"""This file is part of the ethon distribution.
Copyright (c) 2021 vasusen-code
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.
License can be found in < https://github.com/vasusen-code/ethon/blob/main/LICENSE > ."""

#vasusen-code/thechariotoflight/dronebots
#__TG:ChauhanMahesh__
from telethon import events
import html


# ================= SAFE MENTION =================

async def mention(bot, user_id):
    """
    Return mention user dalam format clickable
    """
    try:
        entity = await bot.get_entity(int(user_id))

        # Ambil nama terbaik
        name = getattr(entity, "first_name", None) \
            or getattr(entity, "title", None) \
            or "User"

        # Escape biar gak rusak markdown
        name = html.escape(name)

        return f'<a href="tg://user?id={user_id}">{name}</a>'

    except Exception:
        # fallback kalau gagal ambil entity
        return f'<a href="tg://user?id={user_id}">User</a>'
