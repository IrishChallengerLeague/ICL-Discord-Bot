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
                match_exists = False
                for match_check in self.bot.matches:
                    if match_check.match_id == faceit['payload']['id']:
                        match_exists = True
                        break

                if not match_exists:
                    self.bot.matches.append(Match(faceit['payload']['id']))

                if not self.bot.cogs['CSGO'].check_live.is_running():
                    self.bot.cogs['CSGO'].check_live.start()

            elif faceit['event'] == 'match_status_finished' or faceit['event'] == 'match_status_aborted' or faceit['event'] == 'match_status_cancelled':
                match: Match = None
                for match_check in self.bot.matches:
                    if match_check.match_id == faceit['payload']['id']:
                        match = match_check
                        break

                if match is not None:
                    for member in match.team1_channel.members + match.team2_channel.members:
                        await member.move_to(channel=self.bot.get_channel(784164015122546751), reason=f'Match Complete')
                    self.bot.matches.remove(match)

            return web.Response(status=200)


        else:
            # Used to decline any requests what doesn't match what our
            # API expects.
            self.logger.warning(f'{request.remote} sent an invalid request.')
            return WebServer._http_error_handler("request-type")

        return WebServer._http_error_handler()

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
