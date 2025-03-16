"""Implemenattion of tournament. """

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from game_api_client import GameAPIClient
from sheets_manager import TournamentSheetsManager

@dataclass
class TeamMember:
    """Represents a member of the team. """

    username: str = field(compare=False)
    user_id: int
    discord_id: str
    avatar_url: str = field(compare=False)
    country_emoji: str = field(compare=False)

@dataclass
class Team:
    """Represents a team of the tournament. """

    members: list[TeamMember]
    name: str|None
    avatar_url: str|None
    country_emoji: str|None

    def __contains__(self, user_id: int|str) -> bool:
        for member in self.members:
            if (user_id in [member.user_id, member.discord_id]):
                return True
        return False

@dataclass
class Game:
    """Represents a game of the match. """
    team1_score: int = field(compare=False)
    team2_score: int = field(compare=False)
    game_id: int

@dataclass
class Match:
    """Represents a match of the tournament bracket. """

    stage: str
    number: int
    status: str
    team1: Team|None
    team2: Team|None

    winner: Team|None = field(init=False, default=None)
    score: str = field(init=False, default="0:0")

    match_id: int|None = field(init=False, default=None)
    next_match: Optional["Match"] = field(init=False, default=None)

    games: list[Game] = field(init=False, default_factory=list)
    games_amount: int = field(init=False, default=3)

class MatchManager(ABC):
    """Represents a class for managing the tournament match logic. """

    @staticmethod
    @abstractmethod
    def create_match(
        stage: str,
        number: int,
        status: str,
        team1: Team|None = None,
        team2: Team|None = None
    ) -> Match:
        """Creates an instance of Match. """

    @staticmethod
    @abstractmethod
    def update_match(match: Match, match_info: dict):
        """Updates match information. """

class OsuMatchManager(MatchManager):
    """Represents a class for managing the osu tournament match logic. """

    @staticmethod
    def create_match(
        stage: str,
        number: int,
        status: str,
        team1: Team|None = None,
        team2: Team|None = None
    ) -> Match:
        """Returns an instance of Match. """
        return Match(stage, number, status, team1, team2)

    @staticmethod
    def update_match(match: Match, match_info: dict):
        """Updates match info. """

        for event in match_info["events"]:
            if ("game" not in event) or (not event["game"]["scores"]):
                continue

            team1_score = 0
            team2_score = 0
            game_id = event["id"]

            for score in event["game"]["scores"]:
                if score["user_id"] in match.team1:
                    team1_score += score["score"]
                elif score["user_id"] in match.team2:
                    team2_score += score["score"]

            game = Game(team1_score, team2_score, game_id)

            if game in match.games:
                continue

            match.games.append(game)

            if match.games_amount == len(match.games):
                break

        team1_match_score = 0
        team2_match_score = 0

        for game in match.games:
            if game.team1_score > game.team2_score:
                team1_match_score += 1
                continue
            team2_match_score += 1

        match_score = f"{team1_match_score}:{team2_match_score}"
        if match.score != match_score:
            match.score = match_score

        if team1_match_score >= (match.games_amount // 2 + 1):
            match.winner = match.team1
        elif team2_match_score >= (match.games_amount // 2 + 1):
            match.winner = match.team2

@dataclass
class Bracket:
    """Represents a tournament bracket. """

    matches: list[Match] = field(init=False, default_factory=list)
    loosers: list[Team] = field(init=False, default_factory=list)

class BracketManager(ABC):
    """Represents a class for managing the tournament bracket logic. """

    _bracket: Bracket|None

    def __init__(self, match_manager: MatchManager):
        self._bracket = None
        self._match_manager = match_manager

    @abstractmethod
    def generate_bracket(self, teams: list[Team]):
        """Creates matches with pairs of teams and generates a bracket. """

    @abstractmethod
    def update_matches(self, matches_info: list[dict]) -> bool:
        """Updates information about matches. """

    @abstractmethod
    def enter_match_results(self, match_number: int, winner_number: int, score: str):
        """Enters directly the results of the match. """

    def get_matches(self) -> list[Match]:
        """Bracket matches getter. """
        return self._bracket.matches

class SEBracketManager(BracketManager):
    """
    Represents a class for managing
    the tournament bracket logic in single elimination format.
    """

    def generate_bracket(self, teams: list[Team]):
        """
        Generates a bracket based on creating matches with balanced pairs of team,
        signifies the beginning of the main phase of the tournament, the match phase.

        Args:
            teams (list[Team]): list of participating teams.

        Raises:
            ValueError: if bracket already exists.
        """

        self._bracket = Bracket()

        # TODO: Add support for arbitrary length teams.

        pairs = [] # [{1:16}, {2:15}, {3:14}, ..., {i:N-i+1}]
        # i: team_number (and match number); N: len(teams)

        for match_number in range(1, len(teams) // 2 + 1):
            pair = {}
            pair[match_number] = len(teams) - match_number + 1
            pairs.append(pair)

        balanced_pairs = self._balance_pairs(pairs)[0]

        # Creating the initial matches
        match_number = 1
        for team_number1, team_number2 in balanced_pairs.items():
            team1 = teams[team_number1 - 1]
            team2 = teams[team_number2 - 1]
            match = self._match_manager.create_match(
                len(teams) // 2, match_number, "Pending", team1, team2
            )
            self._bracket.matches.append(match)
            match_number += 1

        # Creating the remaining matches
        for i in range(0, len(teams) - 2, 2):
            match = self._match_manager.create_match(
                self._bracket.matches[i].stage // 2, match_number, "Scheduled"
            )

            self._bracket.matches.append(match)
            self._bracket.matches[i].next_match = match
            self._bracket.matches[i + 1].next_match = match

            match_number += 1

    def update_matches(self, matches_info: list[dict]):
        """Updates information about matches. """

        for match_info in matches_info:
            for match in self._bracket.matches:
                if match.match_id != match_info["match"]["id"]:
                    continue
                self._match_manager.update_match(match, match_info)
                if match.winner is not None:
                    match.status = "Completed"

                if match.next_match is not None:
                    if match.number % 2 != 0:
                        match.next_match.team1 = match.winner
                    else:
                        match.next_match.team2 = match.winner

                    match.next_match.status = "Pending"
                break

    def enter_match_results(self, match_number: int, winner_number: int, score: str):
        """Enters the results of the match. """

        for match in self._bracket.matches:
            if match.number == match_number:
                if winner_number == 1:
                    match.winner = match.team1
                else:
                    match.winner = match.team2

                if match.next_match is not None:
                    if match.number % 2 != 0:
                        match.next_match.team1 = match.winner
                    else:
                        match.next_match.team2 = match.winner
                    match.next_match.status = "Pending"

                match.status = "Completed"
                match.score = score
                break

    def _balance_pairs(self, pairs_of_matches: list[dict]) -> list[dict]:
        """
        Balances the initial pairs of matches so that strong teams (players)
        don't meet in the early stages of the tournament bracket.

        Example:
        [                   [
            {1: 16},           {1: 16,
            {2: 15},            8: 9,
            {3: 14},            4: 13,
            {4: 13},            5: 12,
                        --->
            {5: 12},            2: 15,
            {6: 11},            7: 10,
            {7: 10},            3: 14,
            {8: 9}              6: 11}
        ]                   ]
        """

        pairs = []
        while pairs_of_matches:
            merged_pairs = pairs_of_matches.pop(0) | pairs_of_matches.pop(-1)
            pairs.append(merged_pairs)

        if len(pairs) == 1:
            return pairs
        return self._balance_pairs(pairs)

@dataclass
class Tournament:
    """Represents a tournament. """

    team_length: int

    teams: list[Team] = field(init=False, default_factory=list)

class TournamentManager(ABC):
    """Represents a class for managing the tournament logic. """

    _tournament: Tournament|None
    _bracket_manager: BracketManager|None

    def __init__(self, game_api_client = GameAPIClient):
        self._game_api_client = game_api_client
        self._bracket_manager = None
        self._tournament = None

    def get_teams(self):
        """Tournament teams getter. """
        return self._tournament.teams

    def get_matches(self):
        """bracket matches getter. """
        return self._bracket_manager.get_matches()

    @abstractmethod
    def create_tournament(self, team_length: int):
        """Creates an instance of Tournament, which marks the start of registration stage. """

    @abstractmethod
    def update_teams(self, signups: list[list]) -> bool:
        """Updates teams list based on the signups info. """

    @abstractmethod
    def generate_bracket(self, bracket_manager: BracketManager):
        """Generates a bracket. """

    @abstractmethod
    def enter_match_results(self, match_number: int, winner_number: int, score: str):
        """Enters directly the results of the match. """

    @abstractmethod
    def update_bracket(self) -> bool:
        """Updates information aboout bracket matches. """

class OsuTournamentManager(TournamentManager):
    """Represents a manager for managing the logic of an osu! tournament. """

    def create_tournament(self, team_length: int):
        """
        Creates an instance of Tournament.
        Signifies the beginning of the registration phase.

        Raises:
            ValueError: if Tournament instance already exists.
        """
        self._tournament = Tournament(team_length)

    def update_teams(self, signups: list[list]) -> bool:
        """Updates the teams list when there are new signups. """

        updated = False

        for signup in signups:
            team_members = []
            for i in range(1, self._tournament.team_length * 2, 2):
                osu_id = int(signup[i])
                discord_id = signup[i + 1]

                user_data = self._game_api_client.get_user_info(osu_id)

                username = user_data["username"]
                avatar_url = user_data["avatar_url"]
                country_emoji = self._get_country_emoji(user_data["country_code"])

                team_member = TeamMember(
                        username,
                        osu_id,
                        discord_id,
                        avatar_url,
                        country_emoji
                    )

                if team_member in self._tournament.teams:
                    break

                team_members.append(team_member)

            if len(team_members) != self._tournament.team_length:
                if team_members:
                    # TODO: Need to get the word somehow to host of the tournament
                    # that one of signups is bad.
                    pass
                continue

            updated = True

            self._append_team(
                Team(
                    team_members,
                    team_member.username,
                    team_member.avatar_url,
                    team_member.country_emoji
                )
            )
        return updated

    def generate_bracket(self, bracket_manager: BracketManager):
        """Creates a bracket, signifies the beginning of the playing phase.. """
        self._bracket_manager = bracket_manager
        self._bracket_manager.generate_bracket(self._tournament.teams)

    def update_bracket(self) -> bool:
        """Updates information aboout bracket matches. """

        matches_info = []

        for match in self._bracket_manager.get_matches():
            if match.status in ["Completed", "Scheduled"] or\
                match.status == "Pending" and match.match_id is None:

                continue

            match_info = self._game_api_client.get_match_info(match.match_id)
            matches_info.append(match_info)

        if matches_info:
            self._bracket_manager.update_matches(matches_info)
            return True
        return False

    def enter_match_results(self, match_number: int, winner_number: int, score: str):
        """Enters directly results of the match. """
        self._bracket_manager.enter_match_results(match_number, winner_number, score)

    def _append_team(self, team: Team):
        """Append a team to the teams list. """
        self._tournament.teams.append(team)

    def _get_country_emoji(self, country_code: str) -> str:
        return "".join(chr(127397 + ord(c)) for c in country_code)


class TournamentService:
    """
    Represents a service for interacting between
    tournament data and sheets manager.
    """

    def __init__(
        self,
        sheets_manager: TournamentSheetsManager,
        tournament_manager: TournamentManager
    ):
        self._sheets_manager = sheets_manager
        self._tournament_manager = tournament_manager

    def create_tournament(self, team_length: int = 1):
        """Creates a tournament, signifies the beginning of the registration phase. """
        self._tournament_manager.create_tournament(team_length)

    def update_teams(self):
        """Updates the teams list and teams_sheet. """
        signups = self._sheets_manager.get_signups()
        updated = self._tournament_manager.update_teams(signups)

        if updated:
            teams_info = self._convert_teams_for_updating()
            self._sheets_manager.update_teams_sheet(teams_info)

    def generate_bracket(self, bracket_manager: BracketManager):
        """Creates a tournament bracket, signifies the beginning of the playing phase. """
        self._tournament_manager.generate_bracket(bracket_manager)

    def update_bracket(self):
        """Updates the tournament bracket and bracket_sheet. """
        self._tournament_manager.update_bracket()

        matches_info = self._convert_matches_for_updating()
        self._sheets_manager.update_bracket_sheet(matches_info)

    def connect_match_id(self, match_id: int, discord_id: str):
        """Connects a match id to the corresponding match. """
        matches = self._tournament_manager.get_matches()

        for match in matches:
            if match.team1 is None or match.team2 is None:
                continue

            if match.match_id is not None:
                continue

            if discord_id in match.team1 or discord_id in match.team2:
                match.match_id = match_id
                match.status = "In Progress"

    def enter_match_results(self, match_number: int, winner_number: int, score: str):
        """Enters directly the results of the match. """
        if match_number < 0 or match_number > len(self._tournament_manager.get_matches()):
            raise ValueError("wrong match number")

        if winner_number not in [1, 2]:
            raise ValueError("wrong winner number")

        if len(score) != 3:
            raise ValueError("wrong score format")

        self._tournament_manager.enter_match_results(match_number, winner_number, score)

    def _convert_matches_for_updating(self) -> list[dict]:
        matches_info = []
        matches = self._tournament_manager.get_matches()

        for match in matches:
            match_info = match.__dict__.copy()

            if match_info["team1"] is not None:
                match_info["team1"] = match.team1.__dict__

            if match_info["team2"] is not None:
                match_info["team2"] = match.team2.__dict__

            matches_info.append(match_info)

        return matches_info

    # TODO: Change list[list] to list[dict].
    def _convert_teams_for_updating(self) -> list[list]:
        teams_info = [["", "", "", "Name", "Discord"]]

        teams = self._tournament_manager.get_teams()
        team_counter = 1

        for team in teams:
            team_member = team.members[0]
            teams_info.append(
                [
                    team_counter,
                    f'=IMAGE("{team_member.avatar_url}")',
                    team_member.country_emoji,
                    team_member.username,
                    f"@{team_member.discord_id}"
                ]
            )
            team_counter += 1

        return teams_info
