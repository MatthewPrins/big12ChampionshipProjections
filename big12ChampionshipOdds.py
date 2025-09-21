#!/usr/bin/env python3

# Matthew Prins, 2017-2025
# Big 12 Championship Game Simulator
# Simulates the Big 12 football season and championship game scenarios
# Must use big12GamesImport to create CSV first

import random
import operator
import pandas as pd
import scipy.stats as st
import sys
import csv
from requests_html import HTMLSession
from random import randrange

# Simulation parameters
numberOfRuns = 100000
iowaStateNonConferenceWins = 3  # ISU's non-conference wins to add to total record

# Load list of Big 12 teams
def loadTeamsFromCSV(filename="big12Games.csv"):
    teams = set()
    
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            header = next(reader)  # Skip header row
            
            for row in reader:
                if len(row) >= 2:  # Ensure we have at least team1 and team2
                    teams.add(row[0])  # Add team1
                    teams.add(row[1])  # Add team2
                    
        team_list = sorted(list(teams))
        print(f"Loaded {len(team_list)} teams from CSV: {', '.join(team_list)}")
        return team_list
        
    except FileNotFoundError:
        print(f"ERROR: Could not find {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read teams from {filename}: {e}")
        sys.exit(1)

# Load all Big 12 data from CSV
def loadGameData(filename="big12Games.csv"):
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            header = next(reader)
            rawGames = [[row[0], row[1], float(row[2])] for row in reader]
            
        # Convert to normalized format
        games = []
        for rawGame in rawGames:
            teamName = rawGame[0]
            opponent = rawGame[1] 
            teamWinProbability = rawGame[2]
            
            # Ensure consistent ordering (alphabetically first team, second team)
            if teamName < opponent:
                # teamName is alphabetically first, probability is correct
                games.append([teamName, opponent, teamWinProbability, 0, 0])
            else:
                # opponent is alphabetically first, need to flip probability
                games.append([opponent, teamName, 1.0 - teamWinProbability, 0, 0])
                
        # Verify we have the correct number of games
        expectedGames = 9 * len(bigTwelveTeams) // 2
        if len(games) != expectedGames:
            print(f"ERROR: Expected {expectedGames} games, found {len(games)}. Exiting.")
            sys.exit(1)
            
        print(f"Successfully loaded {len(games)} games")
        
        # Convert 1.0 and 0.0 floats to integers for cleaner processing
        for game in games:
            if game[2] == int(game[2]):
                game[2] = int(game[2])
                
        return games
    
    except FileNotFoundError:
        print(f"ERROR: Could not find {filename}")
        sys.exit(1)

# Initialize team data
def initializeTeamData():
    teams = []
    for teamName in bigTwelveTeams:
        teams.append([teamName, 0, 0, 0, 0, 0, 0])
    return teams

# Initialize championship matchups
def initializeChampionshipMatchups():
    championshipMatchups = []
    for i in range(len(bigTwelveTeams)):
        for j in range(i + 1, len(bigTwelveTeams)):
            championshipMatchups.append([bigTwelveTeams[i], bigTwelveTeams[j], 0])
    return championshipMatchups

# Simulate all Big 12 games
def simulateGames(games, teams):
    # Reset season data for all teams
    for team in teams:
        team[1] = 0  # seasonWins
        team[2] = 0  # tieWins
        team[6] = 0  # currentPlace
    
    # Simulate each game
    for game in games:
        game[3] = 0  # Reset game result
        randomValue = random.random()
        
        # Determine winner based on probability
        for team in teams:
            if game[0] == team[0]:  # Home team
                if randomValue < game[2]:
                    team[1] += 1  # Home team wins
                    game[3] = 1
            elif game[1] == team[0]:  # Away team
                if randomValue >= game[2]:
                    team[1] += 1  # Away team wins

# Find teams with a specific record
def findTeamsWithRecord(teams, wins, excludePlaced=True):
    teamNames = []
    for team in teams:
        if team[1] == wins and (not excludePlaced or team[6] == 0):
            teamNames.append(team[0])
    return sorted(teamNames)

# Get head-to-head record
def getHeadToHeadRecord(games, teams, teamList):
    # Reset tie wins for calculation
    for team in teams:
        team[2] = 0
    
    # Calculate head-to-head wins
    for game in games:
        if game[0] in teamList and game[1] in teamList:
            for team in teams:
                if game[3] == 1 and team[0] == game[0]:  # Home team won
                    team[2] += 1
                elif game[3] == 0 and team[0] == game[1]:  # Away team won
                    team[2] += 1

# Calculate records again common opponents
def getRecordVsCommonOpponents(games, teams, teamList, opponentList):
    # Reset tie wins for calculation
    for team in teams:
        team[2] = 0
    
    # Calculate wins against common opponents
    for game in games:
        for teamName in teamList:
            for opponent in opponentList:
                if game[0] == teamName and game[1] == opponent:
                    for team in teams:
                        if game[3] == 1 and team[0] == teamName:
                            team[2] += 1
                elif game[1] == teamName and game[0] == opponent:
                    for team in teams:
                        if game[3] == 0 and team[0] == teamName:
                            team[2] += 1

# Find opponents that all teams in the list have played
def findCommonOpponents(games, teams, teamList):
    
    # Get each team's opponents
    teamOpponents = []
    for team in teams:
        if team[0] in teamList:
            opponents = []
            for game in games:
                if game[0] == team[0]:
                    opponents.append(game[1])
                elif game[1] == team[0]:
                    opponents.append(game[0])
            teamOpponents.append(opponents)
    
    # Find teams that appear in all opponent lists
    commonOpponents = []
    for team in teams:
        if team[0] not in teamList:
            appearsInAll = all(team[0] in opponentList for opponentList in teamOpponents)
            if appearsInAll:
                commonOpponents.append(team[0])
    
    return commonOpponents

# Calculate strength of schedule (opponents' total wins)
def calculateOpponentStrength(games, teams, teamList):
    
    # Reset tie wins for calculation
    for team in teams:
        team[2] = 0
    
    # Sum opponents' wins for each team
    for game in games:
        for team in teams:
            if game[0] == team[0]:
                # Add away team's wins to home team's opponent strength
                for opponent in teams:
                    if game[1] == opponent[0]:
                        team[2] += opponent[1]
            elif game[1] == team[0]:
                # Add home team's wins to away team's opponent strength
                for opponent in teams:
                    if game[0] == opponent[0]:
                        team[2] += opponent[1]

# Resolve tiebreakers according to Big 12 rules
def resolveTiebreaker(games, teams, tiedTeams):

    usedRandom = False
    winners = sorted(tiedTeams.copy())
    
    if len(winners) == 1:
        return winners, usedRandom
    
    # Two-team tiebreaker
    if len(winners) == 2:
        # Step 1: Head-to-head
        for game in games:
            if game[0] == winners[0] and game[1] == winners[1]:
                if game[3] == 1:
                    winners = [winners[0]]
                else:
                    winners = [winners[1]]
                break
            elif game[0] == winners[1] and game[1] == winners[0]:
                if game[3] == 1:
                    winners = [winners[1]]
                else:
                    winners = [winners[0]]
                break
        
        if len(winners) == 1:
            return winners, usedRandom
        
        # Step 2: Record against next highest placed common opponent
        maxWins = max(team[1] for team in teams)
        
        # Find common opponents
        commonOpponents = findCommonOpponents(games, teams, winners)
        
        recordLevel = maxWins
        while recordLevel >= 0:
            opponentsAtLevel = []
            for team in teams:
                if team[1] == recordLevel and team[0] in commonOpponents:
                    opponentsAtLevel.append(team[0])
            
            if opponentsAtLevel:
                getRecordVsCommonOpponents(games, teams, winners, opponentsAtLevel)
                maxTieWins = max(team[2] for team in teams if team[0] in winners)
                if maxTieWins > 0:
                    newWinners = [team[0] for team in teams 
                                if team[0] in winners and team[2] == maxTieWins]
                    newWinners.sort()
                    if newWinners != winners:
                        winners = newWinners
                        break
            
            recordLevel -= 1
        
        if len(winners) == 1:
            return winners, usedRandom
        
        # Step 3: Record vs all common opponents
        if commonOpponents:
            getRecordVsCommonOpponents(games, teams, winners, commonOpponents)
            maxTieWins = max(team[2] for team in teams if team[0] in winners)
            if maxTieWins > 0:
                newWinners = [team[0] for team in teams 
                            if team[0] in winners and team[2] == maxTieWins]
                newWinners.sort()
                if newWinners != winners:
                    winners = newWinners
        
        if len(winners) == 1:
            return winners, usedRandom
        
        # Step 4: Strength of schedule
        calculateOpponentStrength(games, teams, winners)
        maxStrength = max(team[2] for team in teams if team[0] in winners)
        newWinners = [team[0] for team in teams 
                     if team[0] in winners and team[2] == maxStrength]
        newWinners.sort()
        if newWinners != winners:
            winners = newWinners
        
        if len(winners) == 1:
            return winners, usedRandom
        
        # Step 5: Random selection
        if len(winners) > 1:
            winners = [winners[randrange(len(winners))]]
            usedRandom = True
    
    # Multi-team tiebreaker (3+ teams)
    else:
        while len(winners) > 2:
            # Step 1: Head-to-head among tied teams
            getHeadToHeadRecord(games, teams, winners)
            totalHeadToHeadGames = sum(team[2] for team in teams if team[0] in winners)
            expectedGames = (len(winners) - 1) * len(winners) // 2
            
            if totalHeadToHeadGames == expectedGames:
                # All teams played each other - use head-to-head
                maxWins = max(team[2] for team in teams if team[0] in winners)
                newWinners = [team[0] for team in teams 
                             if team[0] in winners and team[2] == maxWins]
                newWinners.sort()
                if newWinners != winners:
                    winners = newWinners
                    continue
            else:
                # Not all teams played each other - use modified logic from original
                maxPossibleWins = len(winners) - 1
                newWinners = [team[0] for team in teams 
                             if team[0] in winners and team[2] == maxPossibleWins]
                newWinners.sort()
                if newWinners != winners and newWinners:
                    winners = newWinners
                    continue
            
            # Step 2: Record against next highest placed common opponent
            restart = False
            maxWins = max(team[1] for team in teams)
            commonOpponents = findCommonOpponents(games, teams, winners)
            
            recordLevel = maxWins
            while recordLevel >= 0:
                opponentsAtLevel = []
                for team in teams:
                    if team[1] == recordLevel and team[0] in commonOpponents:
                        opponentsAtLevel.append(team[0])
                
                if opponentsAtLevel:
                    getRecordVsCommonOpponents(games, teams, winners, opponentsAtLevel)
                    maxTieWins = max(team[2] for team in teams if team[0] in winners)
                    if maxTieWins > 0:
                        newWinners = [team[0] for team in teams 
                                    if team[0] in winners and team[2] == maxTieWins]
                        newWinners.sort()
                        if newWinners != winners:
                            winners = newWinners
                            restart = True
                            break
                
                recordLevel -= 1
            
            if restart:
                continue
            
            # Step 3: Record vs all common opponents
            if commonOpponents:
                getRecordVsCommonOpponents(games, teams, winners, commonOpponents)
                maxTieWins = max(team[2] for team in teams if team[0] in winners)
                if maxTieWins > 0:
                    newWinners = [team[0] for team in teams 
                                if team[0] in winners and team[2] == maxTieWins]
                    newWinners.sort()
                    if newWinners != winners:
                        winners = newWinners
                        continue
            
            # Step 4: Strength of schedule
            calculateOpponentStrength(games, teams, winners)
            maxStrength = max(team[2] for team in teams if team[0] in winners)
            newWinners = [team[0] for team in teams 
                         if team[0] in winners and team[2] == maxStrength]
            newWinners.sort()
            if newWinners != winners:
                winners = newWinners
                continue
            
            # Step 5: Random selection for 3+ teams
            winners = [winners[randrange(len(winners))]]
            usedRandom = True
            break
        
        # If we're down to 2 teams, use 2-team tiebreaker
        if len(winners) == 2:
            return resolveTiebreaker(games, teams, winners)
    
    return winners, usedRandom

# Determine final standings
def determineStandings(games, teams):
    
    randomTiebreakersUsed = 0
    currentPlace = 1
    
    # Determine 1st and 2nd place
    while currentPlace <= 2:
        maxWins = 0
        for team in teams:
            if team[6] == 0 and team[1] > maxWins:  # Unplaced teams only
                maxWins = team[1]
        
        tiedTeams = findTeamsWithRecord(teams, maxWins, excludePlaced=True)
        
        if tiedTeams:
            winners, usedRandom = resolveTiebreaker(games, teams, tiedTeams)
            if usedRandom:
                randomTiebreakersUsed += 1
            
            # Assign place to winner(s)
            for team in teams:
                if team[0] in winners:
                    team[6] = currentPlace
                    if currentPlace == 1:
                        team[3] += 1  # Increment first place count
                        firstPlaceTeam = team[0]
                    elif currentPlace == 2:
                        team[4] += 1  # Increment second place count
                        secondPlaceTeam = team[0]
        
        currentPlace += 1
    
    return firstPlaceTeam, secondPlaceTeam, randomTiebreakersUsed

# Run the complete Big 12 championship simulation
def runSimulations():
    
    global bigTwelveTeams
    
    print("Starting Big 12 Championship simulation...\n")
    
    # Load teams from CSV first
    bigTwelveTeams = loadTeamsFromCSV()
    
    print(f"Running {numberOfRuns:,} simulations\n")
    
    # Load data and initialize tracking
    games = loadGameData()
    teams = initializeTeamData()
    championshipMatchups = initializeChampionshipMatchups()
    
    # Iowa State specific tracking
    iowaStateWins = [0] * 13  # Track wins by record (0-12 through 12-0)
    iowaStateChampionshipChances = [0] * 13  # Championship game chances by record
    
    totalRandomTiebreakers = 0
    
    # Run simulations
    for simulationNumber in range(numberOfRuns):
        # Simulate the season
        simulateGames(games, teams)
        
        # Determine standings
        firstPlace, secondPlace, randomUsed = determineStandings(games, teams)
        totalRandomTiebreakers += randomUsed
        
        # Track championship matchup
        for matchup in championshipMatchups:
            if ((firstPlace == matchup[0] or firstPlace == matchup[1]) and 
                (secondPlace == matchup[0] or secondPlace == matchup[1])):
                matchup[2] += 1
                break
        
        # Track Iowa State specific data
        for team in teams:
            if team[0] == "Iowa St.":
                conferenceWins = team[1]
                totalWins = conferenceWins + iowaStateNonConferenceWins
                if 0 <= totalWins <= 12:
                    iowaStateWins[totalWins] += 1
                    if firstPlace == "Iowa St." or secondPlace == "Iowa St.":
                        iowaStateChampionshipChances[totalWins] += 1
                break
        
        # Progress update
        if (simulationNumber + 1) % 10000 == 0:
            print(f"Completed {simulationNumber + 1:,} simulations")
    
    return teams, championshipMatchups, iowaStateWins, iowaStateChampionshipChances, totalRandomTiebreakers

# Print simulation results
def printResults(teams, championshipMatchups, iowaStateWins, iowaStateChampionshipChances, totalRandomTiebreakers):
    
    print("\n" + "="*60)
    print("BIG 12 CHAMPIONSHIP SIMULATION RESULTS")
    print("="*60)
    
    # Championship game odds by team
    print("\nCHAMPIONSHIP GAME ODDS:")
    print("-" * 40)
    
    teamsOrdered = []
    for team in teams:
        championshipPercentage = round((team[3] + team[4]) * 100 / numberOfRuns, 1)
        firstPercentage = round(team[3] * 100 / numberOfRuns, 1)
        secondPercentage = round(team[4] * 100 / numberOfRuns, 1)
        
        teamsOrdered.append([
            team[0], 
            championshipPercentage,
            f"{championshipPercentage}% ({firstPercentage}% 1st, {secondPercentage}% 2nd)"
        ])
    
    teamsOrdered.sort(key=lambda x: x[1], reverse=True)
    
    for team in teamsOrdered:
        print(f"{team[0]:<15}: {team[2]}")
    
    # Most likely championship matchups
    print("\nMOST LIKELY CHAMPIONSHIP MATCHUPS:")
    print("-" * 40)
    
    gamesOrdered = []
    for matchup in championshipMatchups:
        if matchup[2] > numberOfRuns * 0.005:  # Only show matchups > 0.5%
            percentage = round(matchup[2] * 100 / numberOfRuns, 1)
            gamesOrdered.append([f"{matchup[0]} vs {matchup[1]}", percentage])
    
    gamesOrdered.sort(key=lambda x: x[1], reverse=True)
    
    for game in gamesOrdered:
        print(f"{game[0]:<30}: {game[1]}%")
    
    # Iowa State specific results
    print("\nIOWA STATE RECORD DISTRIBUTION:")
    print("-" * 40)
    
    for wins in range(13):
        if iowaStateWins[wins] > 0:
            percentage = round(iowaStateWins[wins] * 100 / numberOfRuns, 1)
            losses = 12 - wins
            print(f"{wins}-{losses} record: {percentage}%")
    
    print("\nIOWA STATE CHAMPIONSHIP ODDS BY RECORD:")
    print("-" * 40)
    
    for wins in range(13):
        if iowaStateWins[wins] > 0:
            champPercentage = round(100 * iowaStateChampionshipChances[wins] / iowaStateWins[wins], 1)
            losses = 12 - wins
            print(f"{wins}-{losses} record: {champPercentage}%")
    
    # Simulation statistics
    print("\nSIMULATION STATISTICS:")
    print("-" * 40)
    print(f"Total simulations: {numberOfRuns:,}")
    print(f"Random tiebreakers used: {totalRandomTiebreakers:,}")

def main():
    teams, championshipMatchups, iowaStateWins, iowaStateChampionshipChances, totalRandomTiebreakers = runSimulations()
    printResults(teams, championshipMatchups, iowaStateWins, iowaStateChampionshipChances, totalRandomTiebreakers)

if __name__ == "__main__":
    main()
