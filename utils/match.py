import discord
import logging

from logging.config import fileConfig


class Match:
    def __init__(self, match_id: str):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')

        self.match_id: str = match_id
        self.live: bool = False
        self.team1_channel: discord.VoiceChannel = None
        self.team2_channel: discord.VoiceChannel = None
        self.logger.debug(f'Created match {self.match_id}')

    def set_voice_channels(self, team1_channel: discord.VoiceChannel, team2_channel: discord.VoiceChannel):
        self.team1_channel = team1_channel
        self.team2_channel = team2_channel
        self.logger.debug(
            f'Set voice channels of match {self.match_id} to {self.team1_channel} and {self.team2_channel}')

    def set_live(self):
        self.live = True
        self.logger.debug(f'Match {self.match_id} is live')
