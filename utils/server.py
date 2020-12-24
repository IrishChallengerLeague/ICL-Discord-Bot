import discord
import logging
import pprint
import socket

from aiohttp import web
from json import JSONDecodeError
from logging.config import fileConfig
from typing import List, Union
from utils.match import Match


class WebServer:
    def __init__(self, bot):
        from bot import ICL_bot

        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')

        self.bot: ICL_bot = bot
        self.IP: str = socket.gethostbyname(socket.gethostname())
        self.port: int = self.bot.bot_port
        self.site: web.TCPSite = None

    async def _handler(self, request: web.Request) -> Union[web.Response, web.FileResponse]:
        """
        Super simple HTTP handler.
        Parameters
        ----------
        request : web.Request
            AIOHTTP request object.
        """

        if request.method == 'GET':
            self.logger.debug(f'{request.remote} accessed {self.IP}:{self.port}{request.path}')
            return WebServer._http_error_handler()

        # Auth check for json
        elif request.method == 'POST':
            try:
                faceit = await request.json()
            except JSONDecodeError:
                self.logger.warning(f'{request.remote} sent a invalid json POST ')
                return WebServer._http_error_handler('json-body')

            self.logger.debug(f'request = \n {pprint.pformat(faceit)}')

            if faceit['event'] == 'match_status_ready':
                self.logger.debug(f'{faceit["payload"]["id"]} is ready')
                match_exists = False
                for match_check in self.bot.matches:
                    if match_check.match_id == str(faceit['payload']['id']):
                        match_exists = True
                        self.logger.error('Match already exists')
                        break

                if not match_exists:
                    team1_channel: discord.VoiceChannel = await self.bot.get_channel(
                        787774505854042132).create_voice_channel(
                        name=faceit["payload"]["teams"][0]["name"], user_limit=6)
                    team2_channel: discord.VoiceChannel = await self.bot.get_channel(
                        787774505854042132).create_voice_channel(
                        name=faceit["payload"]["teams"][1]["name"], user_limit=6)

                    team1_roster = []
                    for team1_player in faceit["payload"]["teams"][0]["roster"]:
                        team1_roster.append((team1_player['id'], team1_player['nickname']))

                    team2_roster = []
                    for team2_player in faceit["payload"]["teams"][1]["roster"]:
                        team2_roster.append((team2_player['id'], team2_player['nickname']))

                    team1_invite = await team1_channel.create_invite(max_age=7200)
                    team2_invite = await team2_channel.create_invite(max_age=7200)

                    new_match = Match(faceit['payload']['id'], team1_channel, team2_channel, team1_invite, team2_invite,
                                      faceit["payload"]["teams"][0]["name"], faceit["payload"]["teams"][1]["name"],
                                      team1_roster, team2_roster)
                    self.bot.matches.append(new_match)

                    if not self.bot.cogs['CSGO'].update_scorecard.is_running():
                        self.bot.cogs['CSGO'].update_scorecard.start()

            if faceit['event'] == 'match_status_finished' or faceit['event'] == 'match_status_aborted' or \
                    faceit['event'] == 'match_status_cancelled':
                self.logger.debug(f'{faceit["payload"]["id"]} is over')
                match: Match = None
                for match_check in self.bot.matches:
                    if match_check.match_id == str(faceit['payload']['id']):
                        match = match_check
                        self.logger.error('Match already exists')
                        break

                self.logger.debug(f'Found match {match.match_id}')

                if match is not None:
                    for member in match.team1_channel.members + match.team2_channel.members:
                        await member.move_to(channel=self.bot.get_channel(784164015122546751), reason=f'Match Complete')
                    await match.team2_channel.delete(reason=f'{faceit["payload"]["id"]} Complete')
                    await match.team2_channel.delete(reason=f'{faceit["payload"]["id"]} Complete')
                    self.bot.matches.remove(match)

            self.logger.debug('Sending 200')
            return web.json_response({"received": True}, status=200)

        else:
            # Used to decline any requests what doesn't match what our
            # API expects.
            self.logger.warning(f'{request.remote} sent an invalid request.')
            return WebServer._http_error_handler("request-type")

    async def http_start(self) -> None:
        """
        Used to start the webserver inside the same context as the bot.
        """
        server = web.Server(self._handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        self.site = web.TCPSite(runner, self.IP, self.port)
        await self.site.start()
        self.logger.info(f'Webserver Started on {self.IP}:{self.port}')

    async def http_stop(self) -> None:
        """
        Used to stop the webserver inside the same context as the bot.
        """
        self.logger.warning(f'Webserver Stopping on {self.IP}:{self.port}')
        await self.site.stop()

    @staticmethod
    def _http_error_handler(error: str = 'Undefined Error') -> web.Response:
        """
        Used to handle HTTP error response.
        Parameters
        ----------
        error : bool, optional
            Bool or string to be used, by default False
        Returns
        -------
        web.Response
            AIOHTTP web server response.
        """

        return web.json_response(
            {"error": error},
            status=400 if error else 200
        )
