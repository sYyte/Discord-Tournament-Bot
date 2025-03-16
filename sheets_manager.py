""" Implementing of a google sheets manager class that will interact tournaments sheets. """

from abc import ABC, abstractmethod

import gspread
from oauth2client.service_account import ServiceAccountCredentials

class TournamentSheetsManager(ABC):
    """Represents a manager of sheets related with tournament. """

    @abstractmethod
    def get_signups(self) -> list[list]:
        """Gets the signups list. """

    # TODO: Change list[list] to list[dict]
    @abstractmethod
    def update_teams_sheet(self, teams: list[list]):
        """Updates teams sheet. """

    @abstractmethod
    def update_bracket_sheet(self, matches_info: list[dict]):
        """Updates bracket sheet. """

class OsuTournamentSheetsManager(TournamentSheetsManager):
    """Represents a manager of sheets related with osu tournament. """

    def __init__(
        self,
        spreadsheet_id: str,
        signups_sheet_id: int,
        teams_sheet_id:int,
        bracket_sheet_id:int,
    ):
        self._teams_start_cell = "A1"
        self._bracket_start_cell = "C3"

        self._gspread_client = self._gspread_authorize("key.json")

        self._spreadsheet = self._gspread_client.open_by_key(spreadsheet_id)
        self._signups_sheet = self._spreadsheet.get_worksheet_by_id(signups_sheet_id)
        self._teams_sheet = self._spreadsheet.get_worksheet_by_id(teams_sheet_id)
        self._bracket_sheet = self._spreadsheet.get_worksheet_by_id(bracket_sheet_id)

    def set_teams_start_cell(self, cell: str):
        """
        Set the starting cell of the teams sheet
        to determine where to enter the data.
        """
        self._teams_start_cell = cell

    def set_bracket_start_cell(self, cell: str):
        """
        Set the starting cell of the bracket sheet
        to determine where to enter the data.
        """
        self._bracket_start_cell = cell

    def get_signups(self) -> list[list]:
        """
        Returns the signups list.

        Returns:
            list[list]: signups list 
                e.g. for team length == 1
                [
                    [time_stamp, id, discord_id],
                    ...
                ]
        """
        signups = self._signups_sheet.get_all_values()
        return signups[1:]

    def update_bracket_sheet(self, matches_info: list[dict]):
        """ Updates an information about matches in bracket sheet of main spreadsheet. """

        col = int(chr(int(ord(self._bracket_start_cell[0])) - 16))
        start_row = int(self._bracket_start_cell[1])
        match_index = 0
        stage_number = 1
        stage_step = 11
        match_step = 4

        while match_index < len(matches_info):
            for row in range(start_row, (len(matches_info) + 1) * 2, match_step):
                match_info = matches_info[match_index]
                match_index += 1

                if match_info["status"] == "Scheduled":
                    continue

                if match_info["status"] in ["Completed", "In Progress"]:
                    score_on_sheet = self._bracket_sheet.cell(row + 1, col + 4).value
                    current_score = match_info["score"]
                    if score_on_sheet != current_score:
                        self._bracket_sheet.update_cell(row + 1, col + 4, current_score)
                    continue

                if match_info["team1"] is not None:
                    avatar = self._bracket_sheet.cell(
                        row, col, value_render_option="FORMULA"
                    ).value

                    if not avatar:
                        image = f'=IMAGE("{match_info["team1"]["avatar_url"]}")'
                        country_emoji = match_info["team1"]["country_emoji"]
                        name = match_info["team1"]["name"]

                        self._bracket_sheet.update_cell(row, col, image)
                        self._bracket_sheet.update_cell(row + 1, col + 2, country_emoji)
                        self._bracket_sheet.update_cell(row + 1, col + 3, name)

                if match_info["team2"] is not None:
                    avatar = self._bracket_sheet.cell(
                        row, col + 7, value_render_option="FORMULA"
                    ).value

                    if not avatar:
                        image = f'=IMAGE("{match_info["team2"]["avatar_url"]}")'
                        country_emoji = match_info["team2"]["country_emoji"]
                        name = match_info["team2"]["name"]

                        self._bracket_sheet.update_cell(row + 1, col + 5, name)
                        self._bracket_sheet.update_cell(row + 1, col + 6, country_emoji)
                        self._bracket_sheet.update_cell(row, col + 7, image)

                self._bracket_sheet.update_cell(row + 1, col + 4, "VS")

            match_step *= 2
            start_row += 2 ** stage_number
            col += stage_step
            stage_number += 1

    # TODO Change list[list] to list[dict] and implement updating with list[dict].
    # TODO: Implement updating the teams sheet with using start cell.
    def update_teams_sheet(self, teams: list[list]):
        """
        Updates the teams sheet.

        Args:
            teams (list[list]): information about teams
                e.g. 
                if team_length > 1:
                    [
                        [avatar_url, game_id, discord_id],
                        ...
                    ]
                else:
                    [
                        [
                            team_avatar_url,
                            team_name,
                            member1_avatar_url,
                            member1_game_id,
                            member1_discord_id,
                            member2_avatar_url,
                            member2_game_id,
                            member2_discord_id,
                            ...
                        ],
                        ...
                    ]
        """
        self._teams_sheet.clear()
        self._teams_sheet.append_rows(teams, value_input_option="USER_ENTERED")

    def _gspread_authorize(self, key_path: str):
        """ Authorizes a gspread client. """
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
        return gspread.authorize(creds)
