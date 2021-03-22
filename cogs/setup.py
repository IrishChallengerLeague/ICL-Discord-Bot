import aiohttp
import discord
import logging
import pprint
import re

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
                      brief='Connect your Faceit to the bot', usage='<Faceit Name or Faceit URL>')
    async def link(self, ctx: commands.Context, faceit: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        faceit_nick = faceit
        if re.match(r'.*faceit.com\/.*\/players.*', faceit):
            faceit_nick = faceit[faceit.rfind('players/')+8:]
            if faceit_nick[-1] == '/':
                faceit_nick = faceit_nick[:-1]
        headers = {f'Authorization': f'Bearer {self.bot.faceit_token}'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f'https://open.faceit.com/data/v4/players?nickname={faceit_nick}') as r:
                json_body = await r.json()
                if 'errors' in json_body:
                    raise commands.UserInputError('No user found with that url/nickname')
                faceit_id = json_body['player_id']
                faceit_avatar = json_body['avatar']
                faceit_url: str = json_body['faceit_url'].replace('{lang}', json_body['settings']['language'])
            async with session.get(f'https://open.faceit.com/data/v4/players/{faceit_id}/hubs') as r:
                json_body = await r.json()
                if 'errors' in json_body:
                    raise commands.UserInputError('Error in determining if the user is in the Hub')
                player_in_hub = False
                for hub in json_body['items']:
                    if hub['hub_id'] == 'd9dba8bd-6bf9-435f-bdbc-808ae42d21bd' or hub['hub_id'] == '6a1da082-546e-4f7d-bbe6-54a0e42b9981':
                        player_in_hub = True
                        break
                if not player_in_hub:
                    raise commands.UserInputError(f'You must join the hub before linking your account.')


        db = Database('sqlite:///main.sqlite')
        await db.connect()
        await db.execute('''
                        REPLACE INTO users (discord_id, faceit_id)
                        VALUES( :discord_id, :faceit_id )
                        ''', {"discord_id": str(ctx.author.id), "faceit_id": str(faceit_id)})
        embed = discord.Embed(description=f'Connected to [`{faceit_id}`]({faceit_url})', color=0x00FF00)
        embed.set_author(name=faceit_nick, icon_url=faceit_avatar, url=faceit_url)
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.author} connected to {faceit}')
        await ctx.author.add_roles(ctx.guild.get_role(793186930220597269))
        self.logger.info(f'Added Member role to {ctx.author}')
        await ctx.author.edit(nick=faceit_nick)
        self.logger.info(f'Changed {ctx.author}\'s nickname.')

    @link.error
    async def link_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            self.logger.warning(f'{ctx.author} did not enter a valid Faceit account')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')


def setup(client):
    client.add_cog(Setup(client))
