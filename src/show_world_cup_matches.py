"""
Show FIFA World Cup matches by year
This helps you see which matches you can predict or analyze
"""
import pandas as pd
import sys

# Get year from command line or default to 2026
year = int(sys.argv[1]) if len(sys.argv) > 1 else None

if year == None:
    print("\n" + "=" * 80)
    print(f"💡 Usage: python show_wc2026_matches.py [year]")
    print(f"   Current: FIFA World Cup {year}")
    print(f"   Example: python show_wc2026_matches.py 2022")
    print("=" * 80)
    sys.exit(0)


df = pd.read_csv("data/results.csv", parse_dates=["date"])

# Filter for World Cup matches in the specified year
wc_matches = df[
    (df.tournament == "FIFA World Cup") &
    (df.date.dt.year == year)
].copy()

# Sort by date
wc_matches = wc_matches.sort_values("date")

if wc_matches.empty:
    print(f"No FIFA World Cup matches found for year {year}")
    print("\nUsage: python show_wc2026_matches.py [year]")
    print("Example: python show_wc2026_matches.py 2022")
    sys.exit(0)

print("=" * 80)
print(f"⚽ FIFA WORLD CUP {year} MATCHES")
print("=" * 80)
print(f"Found {len(wc_matches)} matches\n")

# Group by date
for date in wc_matches.date.unique():
    matches_on_date = wc_matches[wc_matches.date == date]
    print(f"\n📅 {date.strftime('%Y-%m-%d (%B %d)')}")
    print("-" * 80)

    for _, match in matches_on_date.iterrows():
        # Show score if available
        if pd.notna(match.home_score) and pd.notna(match.away_score):
            score = f" [{int(match.home_score)}-{int(match.away_score)}]"
            status = "✅"
        else:
            score = " [TBD]"
            status = "⏳"

        venue_info = f" at {match.city}, {match.country}" if pd.notna(match.city) else ""
        neutral = " [NEUTRAL]" if match.neutral else ""

        print(f"  {status} {match.home_team} vs {match.away_team}{score}{venue_info}{neutral}")

        # Suggest command only for unplayed matches
        if pd.isna(match.home_score):
            team1 = f'"{match.home_team}"' if ' ' in match.home_team else match.home_team
            team2 = f'"{match.away_team}"' if ' ' in match.away_team else match.away_team
            print(f"      → python main.py {team1} {team2}")
