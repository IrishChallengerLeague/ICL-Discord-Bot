import discord
import logging
import pprint

from databases import Database
from discord.ext import commands
from logging.config import fileConfig
from typing import List, Dict, Tuple
from utils.server import WebServer

__version__ = '0.0.2'
__dev__ = 784871645483237386


class ICL_bot(commands.Bot):
    def __init__(self, config: dict, startup_extensions: List[str]):
        super().__init__(command_prefix=commands.when_mentioned_or('icl.'), case_insensitive=True, description='ICL Bot',
                         help_command=commands.DefaultHelpCommand(verify_checks=False),
                         intents=discord.Intents(
                             guilds=True, members=True, bans=True, emojis=True, integrations=True, invites=True,
                             voice_states=True, presences=False, messages=True, guild_messages=True, dm_messages=True,
                             reactions=True, guild_reactions=True, dm_reactions=True, typing=True, guild_typing=True,
                             dm_typing=True
                         ))
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')
        self.logger.debug(f'Version = {__version__}')
        self.logger.debug(f'config.json = \n {pprint.pformat(config)}')

        self.token: str = config['discord_token']
        self.faceit_token: str = config['faceit_token']
        self.bot_IP: str = config['bot_IP']
        if 'bot_port' in config:
            self.bot_port: int = config['bot_port']
        else:
            self.bot_port: int = 3000
        self.web_server = WebServer(bot=self)
        self.dev: bool = False
        self.version: str = __version__

        self.matches: List[str] = []
        self.matches_check: List[str] = []

        self.match_channels: Dict[str, Tuple[discord.VoiceChannel, discord.VoiceChannel]] = {}

        for extension in startup_extensions:
            self.load_extension(f'cogs.{extension}')

    async def on_ready(self):
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        await db.execute('''
                    CREATE TABLE IF NOT EXISTS users(
                        discord_id TEXT UNIQUE,
                        faceit_id TEXT
                    )''')

        # TODO: Custom state for waiting for pug or if a pug is already playing
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Activity(type=discord.ActivityType.competing,
                                                             name='ICL'))

        self.dev = self.user.id == __dev__
        self.logger.debug(f'Dev = {self.dev}')

        await self.web_server.http_start()
        self.logger.info(f'{self.user} connected.')

    async def load(self, extension: str):
        self.load_extension(f'cogs.{extension}')

    async def unload(self, extension: str):
        self.unload_extension(f'cogs.{extension}')

    async def close(self):
        self.logger.warning('Stopping Bot')
        await self.web_server.http_stop()
        await super().close()

    def run(self):
        super().run(self.token, reconnect=True)
