import os
import sys

import discord

from dotenv import load_dotenv
from discord.ext import commands;

from modules import *


ENABLED_MODULES = [
    timezones,
    dynamic_channels,
    events,
]

load_dotenv()
TOKEN = os.getenv("TOKEN")

if ("--help" in sys.argv):
    import modules
    print("Usage: `python bot.py`\n(don't forget a `.env` file with discord token)\n\nAvailable modules:")
    print("\n".join("  " + mod for mod in modules.__all__))
    exit(0)

intents = discord.Intents(message_content=True)
for module in ENABLED_MODULES:
    intents |= module.INTENTS

bot = commands.Bot(command_prefix='/', intents=intents)
setattr(bot, "modules", [])

for module in ENABLED_MODULES:
    module.load(bot)


@bot.tree.command(name="help", description="Get help.")
async def help(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("\n".join([
        f"Loaded Modules: {len(bot.modules)}\n",
        "\n".join("  " + line for line in bot.modules),
        "\n"
        "Type `/help-<module>` to get more information on a specific module.",
    ]), ephemeral=True)


@bot.event
async def on_ready():
    print(f"Synced {len(await bot.tree.sync())} commands")


bot.run(TOKEN)