import re
import sqlite3

import discord

from discord import app_commands


INTENTS = discord.Intents(
    guilds=True,
    voice_states=True,
)


PERMISSIONS = discord.PermissionOverwrite.from_pair(
    discord.Permissions.all_channel(),
    discord.Permissions.none(),
)


def load(bot):
    bot.modules += ["**dynamic-channels**: dynamically manage voice channels so multiple groups can all use voice at the same time"]

    @bot.tree.command(name="help-dynamic-channels", description="Information about the **dynamic-channels** module.")
    async def help(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("\n".join([
            "When any user joins the designated Lobby, they will be moved to a newly created voice channel and given permission to rename/manage it. When nobody is left in there, it will be deleted.",
            "",
            "Available commands:",
            "  `/vc-set`: set the channel to be treated as the lobby",
            "  `/vc-remove`: remove a lobby and disable its dynamic voice channels",
            "  `/vc-view`: view which channel was set to be the lobby",
        ]), ephemeral=True)


    with sqlite3.connect("dynamic_channels.db") as db:
        db.row_factory = sqlite3.Row
        if db.execute("SELECT name FROM sqlite_master WHERE name='channels'").fetchone() is None:
            print('initialising dynamic_channel db')
            db.execute("CREATE TABLE channels(id NOT NULL, type, PRIMARY KEY (id))")
            db.commit()
        print('dynamic-channel database connected')


        @bot.event
        async def on_voice_state_update(member, before, after) -> None:
            if member.bot:
                return

            if (channel := after.channel) and db.execute("SELECT * FROM channels WHERE id = ? AND type = 'lobby'", [channel.id]).fetchone():
                new = await member.guild.create_voice_channel(f"{member.display_name}'s Channel", category=channel.category, overwrites={member: PERMISSIONS})
                await member.move_to(new)
                db.execute("INSERT INTO channels VALUES (?, 'ephemeral')", [new.id])
                db.commit()
            elif (channel := before.channel) and db.execute("SELECT * FROM channels WHERE id = ? AND type = 'ephemeral'", [channel.id]).fetchone():
                if not channel.members:
                    await channel.delete()
                    db.execute("DELETE FROM channels WHERE id = ? AND type = 'ephemeral'", [channel.id])
                    db.commit()


        @bot.tree.command(name="vc-set", description="Set the lobby for dynamic voice channels.")
        @app_commands.describe(channel="The channel to serve as a lobby.")
        async def vc_set(interaction: discord.Interaction, channel: discord.VoiceChannel) -> None:
            db.execute("INSERT INTO channels VALUES (?, 'lobby') ON CONFLICT DO NOTHING", [channel.id])
            db.commit()
            await interaction.response.send_message(f"VC lobby set to **{channel.name}**.", ephemeral=True)


        @bot.tree.command(name="vc-remove", description="Remove the lobby for dynamic voice channels.")
        @app_commands.describe(channel="The lobby to remove.")
        async def vc_remove(interaction: discord.Interaction, channel: discord.VoiceChannel) -> None:
            db.execute("DELETE FROM channels WHERE id = ?", [channel.id])
            db.commit()
            await interaction.response.send_message(f"VC lobby **{channel.name}** was removed.", ephemeral=True)


        @bot.tree.command(name="vc-view", description="View the lobby for dynamic voice channels.")
        async def vc_view(interaction: discord.Interaction) -> None:
            msg = ""
            for row in db.execute("SELECT id FROM channels WHERE type = 'lobby'").fetchall():
                if row["id"] in (channel.id for channel in interaction.guild.voice_channels):
                    msg += f"<#{row["id"]}>\n"
            await interaction.response.send_message(msg or "No lobbies set for current server.", ephemeral=True)