import pandas as pd
from functools import lru_cache
from src.tool_registry import ToolRegistry
from datetime import datetime, timedelta

# Create a global registry for all tools
registry = ToolRegistry()

# Global variable to configure data source
_DATA_SOURCE = "data/results.csv"
_ELO_SOURCE = "data/elo_ranking.tsv"

def set_data_source(path: str):
    """Set the data source path and clear cache"""
    global _DATA_SOURCE
    _DATA_SOURCE = path
    load_data.cache_clear()
    load_elo_data.cache_clear()

@lru_cache()
def load_data():
    df = pd.read_csv(_DATA_SOURCE, parse_dates=["date"])
    return df

@lru_cache()
def load_elo_data():
    """Load ELO ranking data"""
    # Column structure: rank_idx, world_rank, country_name, elo_rating, ...
    df = pd.read_csv(_ELO_SOURCE, sep='\t', header=None)
    # Set column names for clarity
    df.columns = ['rank_idx', 'world_rank', 'country', 'elo'] + [f'col_{i}' for i in range(4, len(df.columns))]
    return df

@lru_cache()
def get_all_team_names():
    """Get all unique team names from the dataset"""
    df = load_data()
    home_teams = set(df["home_team"].unique())
    away_teams = set(df["away_team"].unique())
    all_teams = sorted(home_teams | away_teams)
    return all_teams


@registry.register
def get_head_to_head(team_a: str, team_b: str, last_n: int = 10) -> dict:
    """
    Get historical head to head results between two national teams

    team_a: First team name
    team_b: Second team name
    last_n: Number of recent matches to return
    """
    df = load_data()

    h2h = df[
        ((df.home_team == team_a) & (df.away_team == team_b)) |
        ((df.home_team == team_b) & (df.away_team == team_a))
        ].tail(last_n)

    if h2h.empty:
        return {"error": f"No matches found between {team_a} and {team_b}"}

    results = []
    team_a_wins, team_b_wins, draws = 0, 0, 0

    for _, row in h2h.iterrows():
        if row.home_team == team_a:
            goals_a, goals_b = row.home_score, row.away_score
        else:
            goals_a, goals_b = row.away_score, row.home_score

        if goals_a > goals_b:
            winner = team_a
            team_a_wins += 1
        elif goals_b > goals_a:
            winner = team_b
            team_b_wins += 1
        else:
            winner = "draw"
            draws += 1

        results.append({
            "date": str(row.date.date()),
            "score": f"{team_a} {goals_a} - {goals_b} {team_b}",
            "winner": winner,
            "tournament": row.tournament
        })

    return {
        "total_games": len(h2h),
        f"{team_a}_wins": team_a_wins,
        f"{team_b}_wins": team_b_wins,
        "draws": draws,
        "matches": results
    }


@registry.register
def get_recent_form(team: str, last_n: int = 10) -> dict:
    """
    Get a team's recent match results and form

    team: Team name
    last_n: Number of recent matches to return
    """
    df = load_data()

    matches = df[
        (df.home_team == team) | (df.away_team == team)
        ].tail(last_n)

    if matches.empty:
        return {"error": f"No matches found for {team}"}

    results = []
    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0

    for _, row in matches.iterrows():
        is_home = row.home_team == team
        scored = row.home_score if is_home else row.away_score
        conceded = row.away_score if is_home else row.home_score

        goals_scored += scored
        goals_conceded += conceded

        if scored > conceded:
            result = "W"
            wins += 1
        elif scored == conceded:
            result = "D"
            draws += 1
        else:
            result = "L"
            losses += 1

        opponent = row.away_team if is_home else row.home_team
        results.append({
            "date": str(row.date.date()),
            "opponent": opponent,
            "score": f"{scored}-{conceded}",
            "result": result,
            "tournament": row.tournament,
            "venue": "home" if is_home else "away"
        })

    return {
        "team": team,
        "last_n_games": last_n,
        "record": f"{wins}W {draws}D {losses}L",
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "avg_goals_scored": round(goals_scored / len(matches), 2),
        "avg_goals_conceded": round(goals_conceded / len(matches), 2),
        "matches": results
    }


@registry.register
def get_tournament_history(team: str, tournament: str = "FIFA World Cup") -> dict:
    """
    Get a team's historical performance in a tournament like FIFA World Cup

    team: Team name
    tournament: Tournament name
    """
    df = load_data()

    wc = df[
        ((df.home_team == team) | (df.away_team == team)) &
        (df.tournament == tournament)
        ]

    if wc.empty:
        return {"error": f"No {tournament} matches found for {team}"}

    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0

    for _, row in wc.iterrows():
        is_home = row.home_team == team
        scored = row.home_score if is_home else row.away_score
        conceded = row.away_score if is_home else row.home_score

        goals_scored += scored
        goals_conceded += conceded

        if scored > conceded: wins += 1
        elif scored == conceded: draws += 1
        else: losses += 1

    return {
        "team": team,
        "tournament": tournament,
        "total_matches": len(wc),
        "record": f"{wins}W {draws}D {losses}L",
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "first_appearance": str(wc.date.min().date()),
        "last_appearance": str(wc.date.max().date()),
    }


@registry.register
def get_goals_stats(team: str, last_n: int = 20) -> dict:
    """
    Get attacking and defensive goal statistics for a team

    team: Team name
    last_n: Number of recent matches to analyze
    """
    df = load_data()

    matches = df[
        (df.home_team == team) | (df.away_team == team)
        ].tail(last_n)

    if matches.empty:
        return {"error": f"No matches found for {team}"}

    home_games = matches[matches.home_team == team]
    away_games = matches[matches.away_team == team]

    return {
        "team": team,
        "sample_size": len(matches),
        "overall": {
            "avg_scored": round(
                (home_games.home_score.sum() + away_games.away_score.sum()) / len(matches), 2
            ),
            "avg_conceded": round(
                (home_games.away_score.sum() + away_games.home_score.sum()) / len(matches), 2
            ),
        },
        "home": {
            "avg_scored": round(home_games.home_score.mean(), 2) if len(home_games) > 0 else 0,
            "avg_conceded": round(home_games.away_score.mean(), 2) if len(home_games) > 0 else 0,
        },
        "away": {
            "avg_scored": round(away_games.away_score.mean(), 2) if len(away_games) > 0 else 0,
            "avg_conceded": round(away_games.home_score.mean(), 2) if len(away_games) > 0 else 0,
        }
    }


@registry.register
def get_weighted_form(team: str, last_n: int = 20) -> dict:
    """
    Get team's weighted form with recent matches counting more and tournament matches weighted higher

    team: Team name
    last_n: Number of recent matches to analyze
    """
    df = load_data()

    matches = df[
        (df.home_team == team) | (df.away_team == team)
    ].tail(last_n).copy()

    if matches.empty:
        return {"error": f"No matches found for {team}"}

    # Calculate days since each match
    today = datetime.now()
    matches['days_ago'] = (today - matches['date']).dt.days

    # Tournament importance weights
    tournament_weights = {
        "FIFA World Cup": 3.0,
        "FIFA World Cup qualification": 2.0,
        "UEFA Euro": 2.5,
        "UEFA Euro qualification": 1.5,
        "Copa América": 2.5,
        "African Cup of Nations": 2.5,
        "Friendly": 1.0
    }

    weighted_points = 0
    total_weight = 0
    recent_results = []

    for _, row in matches.iterrows():
        is_home = row.home_team == team
        scored = row.home_score if is_home else row.away_score
        conceded = row.away_score if is_home else row.home_score

        # Skip matches with no score (future matches)
        if pd.isna(scored) or pd.isna(conceded):
            continue

        # Calculate days since each match
        days_ago = (today - row.date).days

        # Time decay: more recent = more weight (exponential decay)
        time_weight = 1.0 / (1.0 + days_ago / 365.0)

        # Tournament importance
        tournament = row.tournament
        tournament_weight = tournament_weights.get(tournament, 1.0)

        # Combined weight
        weight = time_weight * tournament_weight

        # Points: Win=3, Draw=1, Loss=0
        if scored > conceded:
            points = 3
            result = "W"
        elif scored == conceded:
            points = 1
            result = "D"
        else:
            points = 0
            result = "L"

        weighted_points += points * weight
        total_weight += weight

        recent_results.append({
            "date": str(row.date.date()),
            "opponent": row.away_team if is_home else row.home_team,
            "result": result,
            "score": f"{scored}-{conceded}",
            "tournament": tournament,
            "days_ago": int(days_ago),
            "weight": round(weight, 2)
        })

    weighted_form_score = weighted_points / total_weight if total_weight > 0 else 0

    return {
        "team": team,
        "weighted_form_score": round(weighted_form_score, 2),
        "max_possible": 3.0,
        "explanation": "Score considers recency (recent matches weighted higher) and tournament importance (World Cup > qualifiers > friendlies)",
        "sample_size": len(matches),
        "recent_matches": recent_results[-5:]  # Show last 5
    }


@registry.register
def get_competitive_record(team: str, years: int = 4) -> dict:
    """
    Get team's record in competitive matches only (excludes friendlies) over recent years

    team: Team name
    years: Number of years to look back
    """
    df = load_data()

    cutoff_date = datetime.now() - timedelta(days=years*365)

    competitive = df[
        ((df.home_team == team) | (df.away_team == team)) &
        (df.date >= cutoff_date) &
        (df.tournament != "Friendly")
    ]

    if competitive.empty:
        return {"error": f"No competitive matches found for {team} in last {years} years"}

    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0

    for _, row in competitive.iterrows():
        is_home = row.home_team == team
        scored = row.home_score if is_home else row.away_score
        conceded = row.away_score if is_home else row.home_score

        # Skip matches with no score (future matches)
        if pd.isna(scored) or pd.isna(conceded):
            continue

        goals_scored += scored
        goals_conceded += conceded

        if scored > conceded:
            wins += 1
        elif scored == conceded:
            draws += 1
        else:
            losses += 1

    total_matches = len(competitive)
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

    return {
        "team": team,
        "period": f"Last {years} years (competitive only)",
        "total_matches": total_matches,
        "record": f"{wins}W {draws}D {losses}L",
        "win_rate": round(win_rate, 1),
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "goal_difference": goals_scored - goals_conceded,
        "avg_goals_scored": round(goals_scored / total_matches, 2) if total_matches > 0 else 0,
        "avg_goals_conceded": round(goals_conceded / total_matches, 2) if total_matches > 0 else 0
    }


@registry.register
def get_neutral_venue_stats(team: str, last_n: int = 20) -> dict:
    """
    Get team's performance at neutral venues (important for World Cup predictions)

    team: Team name
    last_n: Number of recent neutral venue matches to analyze
    """
    df = load_data()

    # Neutral venue matches
    neutral = df[
        ((df.home_team == team) | (df.away_team == team)) &
        (df.neutral == True)
    ].tail(last_n)

    if neutral.empty:
        return {"error": f"No neutral venue matches found for {team}"}

    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0

    for _, row in neutral.iterrows():
        is_home_listed = row.home_team == team
        scored = row.home_score if is_home_listed else row.away_score
        conceded = row.away_score if is_home_listed else row.home_score

        # Skip matches with no score (future matches)
        if pd.isna(scored) or pd.isna(conceded):
            continue

        goals_scored += scored
        goals_conceded += conceded

        if scored > conceded:
            wins += 1
        elif scored == conceded:
            draws += 1
        else:
            losses += 1

    total = len(neutral)

    return {
        "team": team,
        "neutral_venue_matches": total,
        "record": f"{wins}W {draws}D {losses}L",
        "win_rate": round((wins / total * 100), 1) if total > 0 else 0,
        "avg_goals_scored": round(goals_scored / total, 2) if total > 0 else 0,
        "avg_goals_conceded": round(goals_conceded / total, 2) if total > 0 else 0,
        "note": "World Cup matches are played at neutral venues"
    }


@registry.register
def get_elo_rating(team: str, date: str = None) -> dict:
    """
    Get team's current Elo rating and world ranking

    team: Team name (must match country name in data)
    date: Date parameter (currently ignored - returns latest available data)
    """
    elo_df = load_elo_data()

    # Find team in ELO data
    team_row = elo_df[elo_df['country'] == team]

    if team_row.empty:
        # Try case-insensitive match
        team_row = elo_df[elo_df['country'].str.lower() == team.lower()]

    if team_row.empty:
        return {
            "error": f"Team '{team}' not found in Elo ratings",
            "note": "Elo data contains current rankings only. Check team name spelling."
        }

    team_row = team_row.iloc[0]

    result = {
        "team": team_row['country'],
        "elo": int(team_row['elo']),
        "world_rank": int(team_row['world_rank']),
        "note": "Current Elo rating (latest available snapshot)"
    }

    if date:
        result["warning"] = f"Date '{date}' ignored - only current Elo data available"

    return result
