import re
import sqlite3

from datetime import datetime

import discord
import pytz

from discord import app_commands

TIME_FORMATS = [
    (r'[01]\d:[0-6]\d [ap]m', "%I:%M %p"),
    (r'[01]\d:[0-6]\d[ap]m', "%I:%M%p"),
    (r'[01]?\d [ap]m', "%I %p"),
    (r'[01]?\d[ap]m', "%I%p"),
    (r'[012]?\d:[0-6]\d', "%H:%M"),
    (r'[012]?\dh[0-6]\d', "%Hh%M"),
]


def convert_to_utc(dt: datetime, tz: str) -> int:
    dt = pytz.timezone(tz).localize(dt)
    dt = pytz.utc.normalize(dt)
    return int(dt.timestamp())


async def zone_autocomplete(interaction: discord.Interaction, current: str) -> [app_commands.Choice[str]]:
    options = pytz.all_timezones
    return [app_commands.Choice(name=e, value=e) for e in pytz.all_timezones if current.lower() in e.lower()][:25]


def load(bot):
    with sqlite3.connect('timezones.db') as db:
        if db.execute("SELECT name FROM sqlite_master WHERE name='users'").fetchone() is None:
            print('initialising db')
            db.execute("CREATE TABLE users(id NOT NULL, tz, PRIMARY KEY (id))")
            db.commit()
        print('timezone database connected')


        @bot.tree.command(name="tz-set", description="Set your timezone.")
        @app_commands.describe(zone="Your local timezone.")
        @app_commands.autocomplete(zone=zone_autocomplete)
        async def tz_set(interaction: discord.Interaction, zone: str) -> None:
            db.execute(f"INSERT INTO users VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET tz=excluded.tz", (interaction.user.id, zone))
            db.commit()
            await interaction.response.send_message(f'Your timezone is set to {zone}', ephemeral=True)


        @bot.tree.command(name="tz-set-for", description="Set a timezone for another user.")
        @app_commands.describe(zone="The user's local timezone.")
        @app_commands.autocomplete(zone=zone_autocomplete)
        async def tz_set(interaction: discord.Interaction, member: discord.Member, zone: str) -> None:
            db.execute(f"INSERT INTO users VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET tz=excluded.tz", (member.id, zone))
            db.commit()
            await interaction.response.send_message(f"{member.mention}'s timezone is set to {zone}", ephemeral=True)


        @bot.tree.command(name="tz-view", description="View your set timezone.")
        async def tz_view(interaction: discord.Interaction) -> None:
            if tz := db.execute(f"SELECT tz FROM users WHERE id={interaction.user.id}").fetchone():
                await interaction.response.send_message(f'Your timezone is **{tz[0]}**', ephemeral=True)
            else:
                await interaction.response.send_message('You have not set your timezone yet, use `/tz-set`', ephemeral=True)


        @bot.tree.command(name="tz-view-all", description="View all users' set timezones.")
        async def tz_view_all(interaction: discord.Interaction) -> None:
            msg = ""
            for row in db.execute("SELECT id, tz FROM users").fetchall():
                msg += f'<@{row[0]}>: UTC{row[1]}\n'
            await interaction.response.send_message(msg, ephemeral=True)


        @bot.event
        async def on_message(message):
            if message.author.bot:
                return

            tz = db.execute(f"SELECT tz FROM users WHERE id={message.author.id}").fetchone()
            if tz is None:
                return
            tz = tz[0]

            for pattern, fmt in TIME_FORMATS:
                if time := re.match(f".*?\\b({pattern})\\b.*", message.content.lower()):
                    if time := datetime.strptime(time.groups()[0], fmt):
                        dt = datetime.combine(datetime.today(), time.time())
                        await message.reply(f'This is <t:{convert_to_utc(dt, tz)}:t> in your local time ^^')
                        break