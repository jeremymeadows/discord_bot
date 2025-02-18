import sqlite3

from datetime import datetime

import discord

from discord import app_commands


INTENTS = discord.Intents(
    guilds=True,
)

PROFESSIONS = {
    "Elementalist": ["Tempest", "Weaver", "Catalyst"],
    "Engineer": ["Scrapper", "Holosmith", "Mechanist"],
    "Guardian": ["Dragonhunter", "Firebrand", "Willbender"],
    "Mesmer": ["Chronomancer", "Mirage", "Virtuoso"],
    "Necromancer": ["Reaper", "Scourge", "Harbinger"],
    "Ranger": ["Druid", "Soulbeast", "Untamed"],
    "Revenant": ["Herald", "Renegade", "Vindicator"],
    "Thief": ["Daredevil", "Deadeye", "Specter"],
    "Warrior": ["Berserker", "Spellbreaker", "Bladesworn"],
}

class Event:
    title: str
    description: str
    time: str
    commander: str
    team: list[str]

    def __init__(self, *, title="", description="", time="", commander=""):
        self.title = title
        self.description = description
        self.time = time
        self.commander = commander

    def __str__(self) -> str:
        return "\n".join([
            f"**{self.title}**",
            f"{self.description}",
            "\n**Time**:",
            f"{self.time}",
            "\n**Commander**:",
            f"{self.commander}",
            "\n**Party**:",
            "\n".join(self.team or ["No teammates yet :("]),
            "\u200b"
        ])


def load(bot):
    bot.modules += ["**events**: create and manage events and signups"]

    @bot.tree.command(name="help-events", description="Information about the **events** module.")
    async def help(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("\n".join([
            "Allows events to be created with different roles which people can sign up for.",
            "",
            "Available commands:",
            "  `/ev-set-channel`: set the channel which displays the events",
            "  `/ev-create`: create a new event",
            "  `/ev-delete`: delete an event",
        ]), ephemeral=True)


    with sqlite3.connect("data/events.db") as db:
        db.row_factory = sqlite3.Row
        if db.execute("SELECT * FROM sqlite_master").fetchone() is None:
            print("initialising events db")
            db.execute("CREATE TABLE channels(id NOT NULL, guild NOT NULL, PRIMARY KEY (guild))")
            db.execute("CREATE TABLE events(id NOT NULL, title, description, time, commander, PRIMARY KEY (id))")
            db.execute("CREATE TABLE signups(user_id NOT NULL, event_id NOT NULL, spec, notes, PRIMARY KEY(user_id, event_id))")
            db.execute("CREATE TABLE templates(id NOT NULL, guild, data, PRIMARY KEY (id))")
            db.commit()
        print("events database connected")


        @bot.tree.command(name="ev-set-channel", description="Sets the channel to dispay events in.")
        async def ev_set_channel(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
            db.execute("INSERT INTO channels VALUES (?, ?) ON CONFLICT(guild) DO UPDATE SET id=excluded.id", [channel.id, channel.guild.id])
            db.commit()
            await interaction.response.send_message(f"Event channel is set to **{channel.name}**", ephemeral=True)


        @bot.tree.command(name="ev-create", description="Create a new event.")
        async def ev_create(interaction: discord.Interaction, title: str = None, description: str = None, time: str = None) -> None:
            if not (channel := db.execute("SELECT id FROM channels WHERE guild = ?", [interaction.guild.id]).fetchone()):
                await interaction.response.send_message("No event channel set, use `/ev-set-channel` to specify where new events should be posted.", ephemeral=True)
                return
            if not (channel := next(filter(lambda e: e.id == channel["id"], interaction.guild.text_channels))):
                await interaction.response.send_message("The designated events channel cannot be accessed. Use `/ev-set-channel` to specify a new one.", ephemeral=True)
                db.execute("DELETE FROM channels WHERE guild = ?", [interaction.guild.id])
                db.commit()
                return

            event = Event()
            content = ["Creating a new event, type `cancel` to abort.", "\nEnter a Title:"]
            await interaction.response.send_message("\n".join(content), ephemeral=True)

            msg = title or (await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)).content
            event.title = msg
            # await msg.delete()
            content = content[:-1] + [f"\n**Title**: {event.title}", "\nEnter a description:"]
            await interaction.edit_original_response(content="\n".join(content))

            msg = description or (await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)).content
            event.description = msg
            # await msg.delete()
            content = content[:-1] + [f"\n**Description**: {event.description}", "\nEnter a timestamp:"]
            await interaction.edit_original_response(content="\n".join(content))

            msg = time or (await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)).content
            event.time = msg
            # await msg.delete()
            content = content[:-1] + [f"\n**Date**: {event.time}", "\nCreated!"]
            await interaction.edit_original_response(content="\n".join(content))

            event.commander = interaction.user.mention
            event.team = []
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Sign Up / Change", custom_id="signup", style=discord.ButtonStyle.success))
            view.add_item(discord.ui.Button(label="Sign Out", custom_id="signout", style=discord.ButtonStyle.danger))
            post = await channel.send(event, view=view)

            try:
                db.execute("INSERT INTO events VALUES(?, ?, ?, ?, ?)", [post.id, event.title, event.description, event.time, event.commander])
                db.commit()
            except:
                await post.delete()
                await interaction.edit_original_response("Failed to add event to the database.")

            await interaction.followup.send(post.jump_url, ephemeral=True)


        @bot.tree.context_menu(name="mark-complete")
        async def mark_complete(interaction: discord.Interaction, message: discord.Message) -> None:
            content = message.content
            try:
                db.execute("DELETE FROM signups WHERE event_id = ?", [message.id])
                db.execute("DELETE FROM events WHERE id = ?", [message.id])
                db.commit()
            except:
                await interaction.response.send_message("failed to complete event", ephemeral=True)
                return

            await message.edit(content=f"~~{content}~~", view=None)
            await interaction.response.send_message("ok", ephemeral=True, delete_after=0)


        @bot.event
        async def on_interaction(interaction: discord.Interaction) -> None:
            if interaction.type is not discord.InteractionType.component:
                return

            next_view = discord.ui.View()
            emojis = await interaction.guild.fetch_emojis()

            match interaction.data["custom_id"].split("-"):
                case ["signup"]:
                    for prof in PROFESSIONS:
                        icon = next(filter(lambda emoji: prof.lower() in emoji.name.lower(), emojis))
                        next_view.add_item(discord.ui.Button(emoji=icon, custom_id=f"prof-{prof}-{interaction.message.id}"))
                    await interaction.response.send_message("Select your profession:", ephemeral=True, view=next_view)
                case ["prof", prof, event_id]:
                    for spec in [prof] + PROFESSIONS[prof]:
                        icon = next(filter(lambda emoji: spec.lower() in emoji.name.lower(), emojis))
                        next_view.add_item(discord.ui.Button(emoji=icon, custom_id=f"spec-{spec}-{event_id}"))
                    await interaction.response.send_message("Select your specialization:", ephemeral=True, view=next_view)
                case ["spec", spec, event_id]:
                    data = db.execute("SELECT title, description, time, commander FROM events WHERE id = ?", [int(event_id)]).fetchone()
                    icon = next(filter(lambda emoji: spec.lower() in emoji.name.lower(), emojis))
                    db.execute("INSERT INTO signups VALUES (?, ?, ?, ?) ON CONFLICT DO UPDATE SET spec=excluded.spec, notes=excluded.notes", [interaction.user.mention, event_id, f"<:{icon.name}:{icon.id}>", ""])
                    db.commit()

                    event = Event(**data)
                    team = db.execute("SELECT user_id, spec, notes FROM signups WHERE event_id = ?", [event_id]).fetchall()
                    event.team = [f"{row['spec']} {row['user_id']}" + (f" ({row['notes']})" if row["notes"] else "") for row in team]

                    message = await interaction.channel.fetch_message(event_id)
                    await message.edit(content=event)
                    await interaction.response.send_message(f"Registered as {spec}", ephemeral=True)
                case ["backout"]:
                    data = db.execute("SELECT title, description, time, commander FROM events WHERE id = ?", [interaction.message.id]).fetchone()
                    db.execute("DELETE FROM signups WHERE event_id = ? AND user_id = ?", [interaction.message.id, interaction.user.mention])
                    db.commit()

                    event = Event(**data)
                    team = db.execute("SELECT user_id, spec, notes FROM signups WHERE event_id = ?", [interaction.message.id]).fetchall()
                    event.team = [f"{row['spec']} {row['user_id']}" + (f" ({row['notes']})" if row["notes"] else "") for row in team]
                    await interaction.message.edit(content=event)
                    await interaction.response.send_message("Removed from event", ephemeral=True)
                case _:
                    return
