import os

import discord

from dotenv import load_dotenv
from discord.ext import commands;

from modules import *


ENABLED_MODULES = [
    timezones,
    dynamic_channels,
]

load_dotenv()
TOKEN = os.getenv("TOKEN")


intents = discord.Intents.none()
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