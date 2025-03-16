"""Yes"""
import os

import discord
from discord.ext import commands

from gspread.exceptions import APIError

from sheets_manager import OsuTournamentSheetsManager
from game_api_client import OsuAPIClient
from tournament import OsuTournamentManager, TournamentService, SEBracketManager, OsuMatchManager


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

sheets_manager = None

@bot.command()
async def connect_spreadsheet(
    ctx,
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID"),
    signups_sheet_id: int = int(os.getenv("SIGNUPS_SHEET_ID")),
    teams_sheet_id: int = int(os.getenv("TEAMS_SHEET_ID")),
    bracket_sheet_id: int = int(os.getenv("BRACKET_SHEET_ID"))
    ):
    """Soon. """
    global sheets_manager

    sheets_manager = OsuTournamentSheetsManager(
        spreadsheet_id, signups_sheet_id, teams_sheet_id, bracket_sheet_id
    )

    sheets_manager.set_bracket_start_cell("C3")

    await ctx.send("Spreadsheet is connected")

tournament = None

@bot.command()
async def create_tournament(ctx):
    """Soon. """
    global tournament

    osu_api_client = OsuAPIClient(int(os.getenv("CLIENT_ID")), os.getenv("CLIENT_SECRET"))
    osu_tournament_manager = OsuTournamentManager(osu_api_client)

    tournament = TournamentService(sheets_manager,osu_tournament_manager)
    tournament.create_tournament()
    tournament.update_teams()

    await ctx.send("Tournament is created")

@bot.command()
async def generate_bracket(ctx):
    """Soon. """
    match_manager = OsuMatchManager()
    bracket_manager = SEBracketManager(match_manager)
    tournament.generate_bracket(bracket_manager)
    # tournament.update_bracket()

    await ctx.send("Bracket is created")

@bot.command()
async def update_bracket(ctx):
    """ Soon """

    try:
        tournament.update_bracket()
    except APIError as e:
        await ctx.send(f"{ctx.author.mention} Error: {str(e)}, try again in thirty seconds")
        return

    await ctx.send("Bracket and bracket sheet is updated")

@bot.command()
async def connect_match_id(ctx, match_id: int, discord_id: str):
    """ Soon """

    tournament.connect_match_id(match_id, discord_id)
    await ctx.send("Successfull")

@bot.command()
async def enter_match_results(ctx, match_number: int, winner_number: int, score: str):
    """Soon. """

    try:
        tournament.enter_match_results(match_number, winner_number, score)
    except ValueError as e:
        await ctx.send(f"{ctx.author.mention} Error: {str(e)}")
    await ctx.send("Successfull")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
