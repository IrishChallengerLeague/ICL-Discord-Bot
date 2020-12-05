import logging

from databases import Database
from discord.ext import commands
from logging.config import fileConfig

async def voice_channel(ctx: commands.Context):
    if ctx.author.voice is None:
        raise commands.CommandError(message='You must be in a voice channel.')
    return True
