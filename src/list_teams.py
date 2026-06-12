"""
List all valid team names from the dataset
Optionally filter by World Cup year
"""
import sys
import pandas as pd
from tools import get_all_team_names, load_data


def get_world_cup_teams(year: int) -> list:
    """Get teams that participated in FIFA World Cup in a specific year"""
    df = load_data()

    # Filter for FIFA World Cup matches in the given year
    wc_matches = df[
        (df.tournament == "FIFA World Cup") &
        (df.date.dt.year == year)
    ]

    if wc_matches.empty:
        return []

    # Get unique teams from both home and away
    home_teams = set(wc_matches.home_team.unique())
    away_teams = set(wc_matches.away_team.unique())
    all_teams = sorted(home_teams | away_teams)

    return all_teams


def main():
    # Check if year parameter is provided
    year = None
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print(f"❌ Error: '{sys.argv[1]}' is not a valid year")
            print("Usage: python list_teams.py [year]")
            print("Example: python list_teams.py 2022")
            sys.exit(1)

    # Get teams based on whether year is specified
    if year:
        teams = get_world_cup_teams(year)
        if not teams:
            print(f"❌ No FIFA World Cup matches found for year {year}")
            sys.exit(1)
        title = f"TEAMS IN {year} FIFA WORLD CUP ({len(teams)} teams)"
    else:
        teams = get_all_team_names()
        title = f"ALL VALID TEAM NAMES ({len(teams)} teams)"

    print("=" * 80)
    print(f"📋 {title}")
    print("=" * 80)
    print()

    for i, team in enumerate(teams, 1):
        # Add quotes if team name has spaces
        display_name = f'"{team}"' if ' ' in team else team
        print(f"{i:3d}. {display_name}")

    print()
    print("=" * 80)
    print("💡 Use these exact names (with quotes if they contain spaces)")
    print('   Example: python main.py "United States" Mexico')
    if not year:
        print('   To see teams from a specific World Cup: python list_teams.py 2022')
    print("=" * 80)


if __name__ == "__main__":
    main()
