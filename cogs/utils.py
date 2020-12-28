import logging
from logging.config import fileConfig

import aiohttp
import discord
from discord.ext import commands, tasks

from bot import ICL_bot


class Utils(commands.Cog):
    def __init__(self, bot: ICL_bot):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')
        self.logger.debug(f'Loaded {__name__}')

        self.bot: ICL_bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            embed = discord.Embed(color=0x2d8f00)
            embed.add_field(name='Welcome to ICL!', value='Looking forward to seeing you in queue!', inline=False)
            embed.add_field(name='Link your Faceit account to the bot:',
                            value='In <#793194031437054022> `icl.link <faceit account url>`', inline=False)
            embed.add_field(name='Please read over the rules:',
                            value='<#788094657204715541>', inline=False)
            await member.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden):
            self.logger.error(f'Could not send {member} a PM')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: commands.Context, extension: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.load_extension(f'{extension}')
        await msg.edit(content=f'Loaded {extension}')
        self.logger.debug(f'Loaded {extension} via command')

    @load.error
    async def load_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, ImportError) or isinstance(error, commands.ExtensionNotFound) \
                or isinstance(error, commands.CommandInvokeError):
            await ctx.send(':warning: Extension does not exist.')
            self.logger.warning('Extension does not exist')
        else:
            await ctx.send(str(error))
            self.logger.exception('load command exception')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx: commands.Context, extension: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if extension not in ctx.bot.cogs.keys():
            raise commands.CommandError(':warning: Extension does not exist.')
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.unload_extension(f'{extension}')
        await msg.edit(content=f'Unloaded {extension}')
        self.logger.debug(f'Unloaded {extension} via command')

    @unload.error
    async def unload_error(self, ctx: commands.Context, error):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning('Extension does not exist')
        self.logger.exception('unload command exception')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, amount: int):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        await ctx.channel.purge(limit=amount)
        self.logger.debug(f'Purged {amount} in {ctx.channel}')

    @clear.error
    async def clear_error(self, ctx: commands.Context, error):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify an amount of messages to delete')
            self.logger.warning(f'{ctx.author} did not specify number of messages to delete.')
        self.logger.exception('clear command exception')

    @commands.command(aliases=['version', 'v', 'a'], help='This command gets the bot information and version')
    async def about(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        embed = discord.Embed(color=0xff0000)
        embed.add_field(name=f'ICL Bot v{self.bot.version}',
                        value=f'Built by <@125033487051915264>', inline=False)
        await ctx.send(embed=embed)
        self.logger.debug(f'{ctx.author} got bot about info.')


def setup(client):
    client.add_cog(Utils(client))
