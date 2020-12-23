import aiohttp
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

    @tasks.loop(seconds=1.0)
    async def check_live(self):
        matches_left = 0
        for match in self.bot.matches:
            self.logger.debug(f'Checking match {match.match_id}')
            if not match.live:
                self.logger.debug(f'Match {match.match_id} is not live')
                matches_left += 1
                headers = {f'Authorization': f'Bearer {self.bot.faceit_token}'}
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(f'https://open.faceit.com/data/v4/matches/{match.match_id}') as r:
                        json_body = await r.json()

                        if 'results' in json_body:
                            self.logger.debug(f'Match {match.match_id} knife round over')
                            db = Database('sqlite:///main.sqlite')
                            await db.connect()

                            self.logger.debug(f'match request = \n {pprint.pformat(json_body)}')

                            for player in json_body["teams"]["faction1"]["roster"]:
                                data = await db.fetch_one('SELECT discord_id FROM users WHERE faceit_id = :player',
                                                          {"player": str(player['player_id'])})
                                self.logger.debug(f'data: {data.items()}')
                                if len(data) > 0:
                                    discord_player = self.bot.get_user(data[0])
                                    if discord_player is not None:
                                        try:
                                            await discord_player.move_to(channel=match.team1_channel, reason=f'You are on team 1')
                                        except (discord.HTTPException, AttributeError):
                                            self.logger.error(f'Could not move player {discord_player}')

                            self.logger.debug(f'Moved all team1 players to {match.team1_channel}')

                            for player in json_body["teams"]["faction2"]["roster"]:
                                data = await db.fetch_one('SELECT discord_id FROM users WHERE faceit_id = :player',
                                                          {"player": str(player['player_id'])})
                                self.logger.debug(f'data: {data.items()}')
                                if len(data) > 0:
                                    discord_player = self.bot.get_user(data[0])
                                    if discord_player is not None:
                                        try:
                                            await discord_player.move_to(channel=match.team2_channel, reason=f'You are on team 2')
                                        except (discord.HTTPException, AttributeError):
                                            self.logger.error(f'Could not move player {discord_player}')

                            self.logger.debug(f'Moved all team2 players to {match.team2_channel}')
                            match.set_live()
                            matches_left -= 1

        if matches_left == 0:
            self.check_live.cancel()

    @commands.command(aliases=['live', 'live_matches'], help='This command shows the current live matches.',
                      brief='Shows the current live matches')
    async def matches(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        for match in self.bot.matches:
            headers = {f'Authorization': f'Bearer {self.bot.faceit_token}'}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f'https://open.faceit.com/data/v4/matches/{match.match_id}') as r:
                    json_body = await r.json()
                    score_embed = discord.Embed(color=0x00ff00)
                    score_embed.add_field(name=f'{json_body["results"]["score"]["faction1"]}',
                                          value=f'team_{json_body["teams"]["faction1"]["roster"][0]["nickname"]}', inline=True)
                    score_embed.add_field(name=f'{json_body["results"]["score"]["faction2"]}',
                                          value=f'team_{json_body["teams"]["faction2"]["roster"][0]["nickname"]}', inline=True)
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
