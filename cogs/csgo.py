import discord

from bot import ICL_bot
from databases import Database
from discord.ext import commands, tasks

import logging
from logging.config import fileConfig
import pprint

class CSGO(commands.Cog):
    def __init__(self, bot: ICL_bot):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')
        self.logger.debug(f'Loaded {__name__}')

        self.bot: ICL_bot = bot

    @commands.command(hidden=True)
    async def test(self, ctx: commands.Context, *args):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        print(f'test')

    async def match_start(self, ctx: commands.Context, *args):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        db = Database('sqlite:///main.sqlite')
        await db.connect()

        team1 = []
        team2 = []

        team1_channel = await ctx.guild.create_voice_channel(name=f'team_', user_limit=5 + 1)
        team2_channel = await ctx.guild.create_voice_channel(name=f'team_', user_limit=5 + 1)

        for player in team1:
            await player.move_to(channel=team1_channel, reason=f'You are on \'s Team')
            data = await db.fetch_one('SELECT faceit_id FROM users WHERE discord_id = :player',
                                      {"player": str(player.id)})
        self.logger.debug(f'Moved all team1 players to {team1_channel}')

        for player in team2:
            await player.move_to(channel=team2_channel, reason=f'You are on \'s Team')
            data = await db.fetch_one('SELECT faceit_id FROM users WHERE discord_id = :player',
                                      {"player": str(player.id)})
        self.logger.debug(f'Moved all team2 players to {team2_channel}')

    @commands.command(aliases=['live', 'live_matches'], help='This command shows the current live matches.',
                      brief='Shows the current live matches')
    async def matches(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        for server in self.bot.servers:
            if not server.available:
                score_embed = discord.Embed(color=0x00ff00)
                score_embed.add_field(name=f'{server.team_scores[0]}',
                                      value=f'{server.team_names[0]}', inline=True)
                score_embed.add_field(name=f'{server.team_scores[1]}',
                                      value=f'{server.team_names[1]}', inline=True)
                gotv = server.get_gotv()
                if gotv is None:
                    score_embed.add_field(name='GOTV',
                                          value='Not Configured',
                                          inline=False)
                else:
                    score_embed.add_field(name='GOTV',
                                          value=f'connect {server.server_address}:{gotv}',
                                          inline=False)
                score_embed.set_footer(text="🟢 Live")
                await ctx.send(embed=score_embed)

    @matches.error
    async def matches_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        self.logger.exception(f'{ctx.command} caused an exception')


def setup(client):
    client.add_cog(CSGO(client))
