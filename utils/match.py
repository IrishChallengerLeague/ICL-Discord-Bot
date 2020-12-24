import discord
import logging

from logging.config import fileConfig
from typing import List, Tuple


class Match:
    def __init__(self, match_id: str, team1_channel: discord.VoiceChannel, team2_channel: discord.VoiceChannel,
                 team1_invite: discord.Invite, team2_invite: discord.Invite, team1_name: str, team2_name: str,
                 team1_roster: List[Tuple[str, str]], team2_roster: List[Tuple[str, str]]):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'ICL_bot.{__name__}')

        self.match_id: str = match_id
        self.match_scorecard: discord.Message = None
        self.team1_channel: discord.VoiceChannel = None
        self.team2_channel: discord.VoiceChannel = None
        self.team1_invite: discord.Invite = team1_invite
        self.team2_invite: discord.Invite = team2_invite
        self.team1_channel: discord.VoiceChannel = team1_channel
        self.team2_channel: discord.VoiceChannel = team2_channel
        self.logger.debug(
            f'Set voice channels of match {self.match_id} to {self.team1_channel} and {self.team2_channel}')
        self.team1_name: str = team1_name
        self.team2_name: str = team2_name
        self.team1_score: int = 0
        self.team2_score: int = 0
        self.team1_roster: List[Tuple[str, str]] = team1_roster
        self.team2_roster: List[Tuple[str, str]] = team2_roster
        self.notified_players: bool = False
        self.logger.debug(f'Created match {self.match_id}')

    def update_scores(self, team1_score: int, team2_score: int):
        self.team1_score = team1_score
        self.team2_score = team2_score
