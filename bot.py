import os

import discord

from dotenv import load_dotenv
from discord.ext import commands;

import modules.timezones as timezones
import modules.dynamic_channels as dynchannels

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.none()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)
setattr(bot, "modules", [])

timezones.load(bot)
dynchannels.load(bot)


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