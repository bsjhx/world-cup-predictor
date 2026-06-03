import pandas as pd
from functools import lru_cache

@lru_cache()
def load_data():
    df = pd.read_csv("data/results.csv", parse_dates=["date"])
    # normalize team names to avoid "USA" vs "United States" issues
    df["home_team"] = df["home_team"].str.strip()
    df["away_team"] = df["away_team"].str.strip()
    return df


def get_head_to_head(team_a: str, team_b: str, last_n: int = 10) -> dict:
    """Returns historical head to head record between two teams"""
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


def get_recent_form(team: str, last_n: int = 10) -> dict:
    """Returns a team's recent match results"""
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


def get_tournament_history(team: str, tournament: str = "FIFA World Cup") -> dict:
    """Returns a team's history in a specific tournament"""
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


def get_goals_stats(team: str, last_n: int = 20) -> dict:
    """Returns attacking and defensive stats for a team"""
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