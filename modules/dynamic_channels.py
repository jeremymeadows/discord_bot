import re
import sqlite3

from datetime import datetime

import discord

from discord import app_commands


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
            "  `/vc-set-lobby`: set the channel to be treated as the lobby",
            "  `/vc-remove-lobby`: remove the specific lobby and disable its dynamic voice channels",
        ]), ephemeral=True)


    with sqlite3.connect("dynamic_channels.db") as db:
        db.row_factory = sqlite3.Row
        if db.execute("SELECT name FROM sqlite_master WHERE name='channels'").fetchone() is None:
            print('initialising dynamic_channel db')
            db.execute("CREATE TABLE channels(id NOT NULL, type, PRIMARY KEY (id))")
            db.commit()
        print('dynamic-channel database connected')


        @bot.event
        async def on_voice_state_update(member, before, after):
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


        @bot.tree.command(name="vc-set-lobby", description="Set the lobby for dynamic voice channels.")
        async def vc_set_lobby(interaction: discord.Interaction, channel: discord.VoiceChannel) -> None:
            db.execute(f"INSERT INTO channels VALUES (?, 'lobby') ON CONFLICT DO NOTHING", [channel.id])
            db.commit()
            await interaction.response.send_message(f"VC lobby set to **{channel.name}**.", ephemeral=True)


        @bot.tree.command(name="vc-remove-lobby", description="Remove the lobby for dynamic voice channels.")
        async def vc_remove_lobby(interaction: discord.Interaction, channel: discord.VoiceChannel) -> None:
            db.execute(f"DELETE FROM channels WHERE id = ?", [channel.id])
            db.commit()
            await interaction.response.send_message(f"VC lobby **{channel.name}** was removed.", ephemeral=True)