import os

import discord

from dotenv import load_dotenv
from discord.ext import commands;

import modules.timezones as timezones

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.none()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.tree.command(name="help", description="Get help.")
async def help(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Timezones confuse me. If you use my `/settz` command, then I'll learn your local time and add you to my database. If you post a message with something that looks like a time, then I'll convert it to a discord timestamp to make you easier to understand!", ephemeral=True)


@bot.event
async def on_ready():
    print(f"Synced {len(await bot.tree.sync())} commands")


timezones.load(bot)

bot.run(TOKEN)