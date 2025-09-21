#!/usr/bin/env python3

# Matthew Prins, 2017-2025
# Imports game results and projections from Massey Ratings and writes them to a CSV file for further calculations

import json
import time
from requests_html import HTMLSession

# Games between conference teams to exclude from the conference games list
# Make sure "St" doesn't have a period
nonConferenceGames = [["Arizona", "Kansas St"]]

"""
To get the team ID for a new team:
1. Go to the team's Massey page (e.g. https://masseyratings.com/cf2024/557)
2. Open Chrome Developer Tools > Network > Fetch/XHR
3. Find a request starting with "team.php?..." 
4. Copy the "argv=" parameter value from the request URL
"""

# Big 12 Conference teams with their Massey Ratings team IDs
bigTwelveTeams = [
    ["Arizona", "BDi7A3ZPSjMpkm-28gHmTntaudCa1hvJw9MUw6izmhCxF30P1MEkfs_TtP_tUqkM"],
    ["Arizona St", "BDi7A3ZPSjMpkm-28gHmTqeegXyqgx8Nnv-hwejJf3exF30P1MEkfs_TtP_tUqkM"],
    ["Baylor", "BDi7A3ZPSjMpkm-28gHmTjPzLbqLP9y4S90EI_NuZs2xF30P1MEkfs_TtP_tUqkM"],
    ["BYU", "82gs7NSi9H-KA37ZSGOo7UYdNVbJFpLPrQ763hzcotGxF30P1MEkfs_TtP_tUqkM"],
    ["Cincinnati", "BDi7A3ZPSjMpkm-28gHmTg8YW_vA-E_syjEWUc-kAW2KZUYWCGwYG-4hWKV8TT4Q"],
    ["Colorado", "BDi7A3ZPSjMpkm-28gHmTlhJHoeUC-Nw0lY590VlTRuKZUYWCGwYG-4hWKV8TT4Q"],
    ["Houston", "BDi7A3ZPSjMpkm-28gHmTr8d5Bno8ew-tnXQUivjVjuKZUYWCGwYG-4hWKV8TT4Q"],
    ["Iowa St", "BDi7A3ZPSjMpkm-28gHmTsjdxJ2DIsBDfsFxqj5zDXGKZUYWCGwYG-4hWKV8TT4Q"],
    ["Kansas", "BDi7A3ZPSjMpkm-28gHmTlUchB92AFJzHPKaZwBX776KZUYWCGwYG-4hWKV8TT4Q"],
    ["Kansas St", "BDi7A3ZPSjMpkm-28gHmTobAYZN58qo6xBWEtEkcPhaKZUYWCGwYG-4hWKV8TT4Q"],
    ["Oklahoma St", "BDi7A3ZPSjMpkm-28gHmTj5ixHGzsezYq4S1FxHzuOGKZUYWCGwYG-4hWKV8TT4Q"],
    ["TCU", "BDi7A3ZPSjMpkm-28gHmTlQsL0OgMDlRqqUDUO0eVySxF30P1MEkfs_TtP_tUqkM"],
    ["Texas Tech", "BDi7A3ZPSjMpkm-28gHmTuKBvsalfytVBEDa1S4cjUCxF30P1MEkfs_TtP_tUqkM"],
    ["UCF", "BDi7A3ZPSjMpkm-28gHmTgMXY-J8kJdhldSdvpbo_tWKZUYWCGwYG-4hWKV8TT4Q"],
    ["Utah", "82gs7NSi9H-KA37ZSGOo7V59cu220eKr0aWAeE-Bj1yKZUYWCGwYG-4hWKV8TT4Q"],
    ["West Virginia", "82gs7NSi9H-KA37ZSGOo7U_aIYq9sJfJFOJzsJW_OGKKZUYWCGwYG-4hWKV8TT4Q"]
]

# Check if games between conference teams is actually a non-conference game
def isNonConferenceGame(team1, team2):
    for excludedGame in nonConferenceGames:
        if (team1 == excludedGame[0] and team2 == excludedGame[1]) or \
           (team1 == excludedGame[1] and team2 == excludedGame[0]):
            return True
    return False

# Fetch and parse games for a team from Massey
def fetchTeamGames(teamName, teamId):
    print(f"Getting data for {teamName}...")
    
    session = HTMLSession()
    url = f"https://masseyratings.com/json/team.php?argv={teamId}&task=json"
    response = session.get(url)
    
    try:
        gameData = json.loads(response.html.html)["DI"]
        print(f"Successfully imported {teamName} data")
        return gameData
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error fetching data for {teamName}: {e}")
        return []

# Pase game probability/result into standardized format
def parseGameResult(game, teamName):
    opponent = game[3][0]
    result = game[7][0]
    
    if result == "W":
        winProbability = 1.0
    elif result == "L":
        winProbability = 0.0
    else:
        # Handle projected games with win probability (e.g. "65%")
        try:
            winProbability = float(result[:-1]) / 100
        except ValueError:
            print(f"Warning: Could not parse result '{result}' for {teamName} vs {opponent}")
            winProbability = 0.0
    
    return [teamName, opponent, winProbability]

# Add periods to team names ending with "St" for my sanity
def standardizeTeamNames(games):
    for game in games:
        for i in range(2):
            if game[i].endswith(" St"):
                game[i] = game[i] + "."

# Make sure game counts are correct
def validateGameCounts(games):
    expectedGames = 9 * len(bigTwelveTeams) // 2
    if len(games) != expectedGames:
        print(f"Warning: Expected {expectedGames} games but found {len(games)} games")
    
    # Count games per team
    teamGameCounts = {}
    for game in games:
        team1, team2 = game[0], game[1]
        teamGameCounts[team1] = teamGameCounts.get(team1, 0) + 1
        teamGameCounts[team2] = teamGameCounts.get(team2, 0) + 1
    
    print("\nGame count verification:")
    for teamName, _ in bigTwelveTeams:
        standardizedName = teamName + "." if teamName.endswith(" St") else teamName
        gameCount = teamGameCounts.get(standardizedName, 0)
        if gameCount != 9:
            print(f"Warning: {standardizedName} has {gameCount} games instead of 9")
        else:
            print(f"{standardizedName}: {gameCount} games")

# Export games to CSV
def exportGamesToCsv(games, fileName="big12Games.csv"):
    with open(fileName, "w") as file:
        file.write("teamName,opponent,teamPercentage\n")
        for game in games:
            file.write(",".join(str(field) for field in game) + "\n")
    
    print(f"\nData exported to {fileName}")

def main():
    print("Starting Big 12 football data import...\n")
    
    games = []
    
    for teamName, teamId in bigTwelveTeams:
        # Fetch raw game data from Massey
        rawGames = fetchTeamGames(teamName, teamId)
        
        # Process each game for this team
        for game in rawGames:
            opponent = game[3][0]
            
            # Only include Big 12 vs Big 12 games
            if any(team[0] == opponent for team in bigTwelveTeams) and opponent > teamName:
                # Check if game between conference opponents should be excluded as non-conference
                if not isNonConferenceGame(teamName, opponent):
                    parsedGame = parseGameResult(game, teamName)
                    games.append(parsedGame)
        
        print(f"Current games list has {len(games)} entries\n")
        time.sleep(3)
    
    # Add periods to "St" teams
    standardizeTeamNames(games)
    
    # Validate game counts
    validateGameCounts(games)
    
    # Export to CSV
    exportGamesToCsv(games)
    
    print(f"Processed {len(games)} Big 12 conference games")

if __name__ == "__main__":
    main()
