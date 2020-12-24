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
    async def update_scorecard(self):
        self.logger.debug('Scorecard loop')
        for match in self.bot.matches:
            self.logger.debug(f'found match {match.match_id}')
            headers = {f'Authorization': f'Bearer {self.bot.faceit_token}'}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f'https://open.faceit.com/data/v4/matches/{match.match_id}') as r:
                    json_body = await r.json()
                    self.logger.debug(f'Request on match = \n {pprint.pformat(json_body)}')
                    first_message = True
                    team1_score = 0
                    team2_score = 0
                    if 'results' in json_body:
                        team1_score: int = json_body['results']['score']['faction1']
                        team2_score: int = json_body['results']['score']['faction1']
                        first_message = False

                    if team1_score != match.team1_score or team2_score != match.team2_score or first_message:
                        self.logger.debug('Updating Scores')
                        match.update_scores(team1_score, team2_score)
                        team1_string = f'[Click here]({match.team1_invite.url}) to join voice channel'
                        team2_string = f'[Click here]({match.team2_invite.url}) to join voice channel'

                        db = Database('sqlite:///main.sqlite')
                        await db.connect()

                        for team1_player in match.team1_roster:
                            team1_string += f'\n{team1_player[1]}'

                        for team2_player in match.team2_roster:
                            team2_string += f'\n{team2_player[1]}'

                        embed = discord.Embed()
                        embed.add_field(name=f'{match.team1_score} | {match.team1_name}', value=team1_string,
                                        inline=True)
                        embed.add_field(name=f'{match.team1_score} | {match.team1_name}', value=team2_string,
                                        inline=True)
                        if json_body['status'] != 'FINISHED':
                            embed.set_footer(text="🟢 Live")
                        else:
                            embed.set_footer(text="🟥 Finished")

                        if not match.notified_players:
                            self.logger.debug('First Message')
                            notification_string = ''
                            for player in match.team1_roster + match.team2_roster:
                                data = await db.fetch_one('SELECT discord_id FROM users WHERE faceit_id = :player',
                                                          {"player": str(player[0])})
                                if len(data) > 0:
                                    notification_string += f'<@{data[0]}> '

                            channel: discord.TextChannel = self.bot.get_channel(784437653894332467)
                            message = await channel.send(content=notification_string, embed=embed)
                            match.match_scorecard = message
                            match.notified_players = True
                        else:
                            await match.match_scorecard.edit(embed=embed)

        if len(self.bot.matches) is 0:
            self.logger.debug('canceling')
            self.update_scorecard.cancel()

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
                                          value=f'team_{json_body["teams"]["faction1"]["roster"][0]["nickname"]}',
                                          inline=True)
                    score_embed.add_field(name=f'{json_body["results"]["score"]["faction2"]}',
                                          value=f'team_{json_body["teams"]["faction2"]["roster"][0]["nickname"]}',
                                          inline=True)
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
