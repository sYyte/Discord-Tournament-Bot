"""Request match info"""

from abc import ABC, abstractmethod

import os
import json
import requests

class GameAPIClient(ABC):
    """
    Represents an Interface for api client classes created
    to get information from game APIs.
    """

    @abstractmethod
    def get_user_info(self, user_id: int|str):
        """Gets user info. """

    @abstractmethod
    def get_match_info(self, match_id: int|str):
        """Gets match info. """

class OsuAPIClient(GameAPIClient):
    """
    Represents a client for retrieveing match data, user data and other
    osu! information.
    """

    def __init__(self, client_id: int, client_secret: str):
        self.__access_token = self.__get_access_token(client_id, client_secret)

    def __get_access_token(self, client_id: str, client_secret: str):
        """ Soon """

        url = "https://osu.ppy.sh/oauth/token"
        data = {
            "client_id" : client_id,
            "client_secret" : client_secret,
            "grant_type" : "client_credentials",
            "scope" : "public"
        }

        response = requests.post(url=url, json=data, timeout=5)
        return response.json().get("access_token")

    def get_user_info(self, user_id: int) -> dict:
        """
        Get information about user.

        Args:
            user_id (int): id of an osu user

        Returns:
            dict: information about osu user
        """

        url = f"https://osu.ppy.sh/api/v2/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.__access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)
        return response.json()

    def get_match_info(self, match_id: int) -> dict:
        """ Get information about match by match_id.

        Args:
            match_id (str): id of an osu multiplayer match.

        Returns:
            dict: full match information.
        """

        url = f"https://osu.ppy.sh/api/v2/matches/{match_id}"
        headers = {
            "Authorization": f"Bearer {self.__access_token}"
        }

        response = requests.get(url, headers=headers, timeout=10    )
        return response.json()
