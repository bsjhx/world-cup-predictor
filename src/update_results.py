"""
Update match results in results.csv with actual scores from updated_results.csv
"""

import pandas as pd


def load_updated_results(file_path: str) -> pd.DataFrame:
    """
    Load updated_results.csv without ID column

    Args:
        file_path: Path to the updated results CSV file

    Returns:
        DataFrame with updated match results
    """
    # Keep "NA" as string, don't convert to NaN
    df = pd.read_csv(file_path, parse_dates=["date"], keep_default_na=False, na_values=[''])
    return df


def update_matches(results_df: pd.DataFrame, updated_df: pd.DataFrame, verbose: bool = True) -> tuple:
    """
    Update NA matches in results_df with scores from updated_df

    Matches are identified by (date, home_team, away_team) since updated_df lacks ID column.
    ONLY updates home_score and away_score columns, preserving all other columns exactly.

    Args:
        results_df: Original results DataFrame with ID column
        updated_df: Updated results DataFrame without ID column
        verbose: Print progress messages

    Returns:
        Tuple of (updated_df, stats_dict)
        - updated_df: DataFrame with updated scores
        - stats_dict: Dictionary with counts {updated_count, skipped_count, not_found_count}
    """
    stats = {
        'updated_count': 0,
        'skipped_count': 0,
        'not_found_count': 0
    }

    # Create a copy to avoid modifying the original
    updated_results = results_df.copy()

    # Find all NA matches in results_df (check for string "NA", not NaN)
    na_mask = (results_df['home_score'] == 'NA') & (results_df['away_score'] == 'NA')
    na_matches = results_df[na_mask]

    if verbose:
        print(f"\n🔍 Found {len(na_matches)} matches with NA scores in results.csv")
        print(f"📋 Processing updates from {len(updated_df)} records in updated file...\n")

    # Process each NA match
    for idx, row in na_matches.iterrows():
        match_date = row['date']
        home_team = row['home_team']
        away_team = row['away_team']

        # Search for matching record in updated_df
        match_filter = (
            (updated_df['date'] == match_date) &
            (updated_df['home_team'] == home_team) &
            (updated_df['away_team'] == away_team)
        )
        matches = updated_df[match_filter]

        if len(matches) == 0:
            # No match found in updated file
            stats['not_found_count'] += 1
            if verbose:
                print(f"⚠️  Not found: {match_date.strftime('%Y-%m-%d')} - {home_team} vs {away_team}")
        else:
            # Use first match if multiple found
            match = matches.iloc[0]

            # Check if the match in updated file has actual scores (not "NA" string)
            if match['home_score'] == 'NA' or match['away_score'] == 'NA':
                # Still NA in updated file, skip
                stats['skipped_count'] += 1
                if verbose:
                    print(f"⏭️  Skipped: {match_date.strftime('%Y-%m-%d')} - {home_team} vs {away_team} (still NA)")
            else:
                # Update ONLY the scores - preserve all other columns as-is
                updated_results.at[idx, 'home_score'] = match['home_score']
                updated_results.at[idx, 'away_score'] = match['away_score']
                stats['updated_count'] += 1
                if verbose:
                    score = f"{int(match['home_score'])}-{int(match['away_score'])}"
                    print(f"✅ Updated: {match_date.strftime('%Y-%m-%d')} - {home_team} vs {away_team} ({score})")

    return updated_results, stats


def save_updated_results(df: pd.DataFrame, output_file: str):
    """
    Save updated results to CSV, preserving the exact format of the neutral column

    Args:
        df: DataFrame to save
        output_file: Output file path
    """
    # Sort by ID for consistency
    df_sorted = df.sort_values('id')

    # Convert neutral column to proper boolean representation (True/False not TRUE/FALSE)
    # Since keep_default_na=False loads everything as strings, neutral is "False"/"True" string
    # We need to ensure it stays that way when saving
    if 'neutral' in df_sorted.columns:
        # Map boolean/string values to capitalized strings to match original format
        df_sorted = df_sorted.copy()
        # Standardize to the original CSV format (capitalized: False/True, not FALSE/TRUE)
        df_sorted['neutral'] = df_sorted['neutral'].map(
            lambda x: 'False' if (x == False or x == 'False' or x == 'FALSE' or str(x).lower() == 'false')
            else 'True' if (x == True or x == 'True' or x == 'TRUE' or str(x).lower() == 'true')
            else x
        )

    # Save to CSV
    df_sorted.to_csv(output_file, index=False)

    print(f"\n💾 Saved updated results to: {output_file}")
