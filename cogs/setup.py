import discord
import logging

from bot import ICL_bot
from databases import Database
from discord.ext import commands
from logging.config import fileConfig


class Setup(commands.Cog):
    def __init__(self, bot: ICL_bot):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')
        self.bot: ICL_bot = bot

        self.logger.debug(f'Loaded {__name__}')

    @commands.command(aliases=['login'],
                      help='This command connects users Faceit accounts to the bot.',
                      brief='Connect your Faceit to the bot', usage='<SteamID or CommunityURL>')
    async def link(self, ctx: commands.Context, faceit_id: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')

        db = Database('sqlite:///main.sqlite')
        await db.connect()
        await db.execute('''
                        REPLACE INTO users (discord_id, faceit_id)
                        VALUES( :discord_id, :faceit_id )
                        ''', {"discord_id": str(ctx.author.id), "faceit_id": str(faceit_id)})
        embed = discord.Embed(description=f'Connected {ctx.author.mention} \n `{faceit_id}`', color=0x00FF00)
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.author} connected to {faceit_id}')

    @link.error
    async def link_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            self.logger.warning(f'{ctx.author} did not enter a valid SteamID')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')


def setup(client):
    client.add_cog(Setup(client))
