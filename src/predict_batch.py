"""
Batch prediction module for predicting all NA matches up to a given ID
"""
import pandas as pd
import time
import re
from pathlib import Path
from src.agent import run_agent
from src.tools import load_data


def load_na_matches(max_id: int) -> pd.DataFrame:
    """
    Load all matches with NA scores up to (and including) max_id

    Args:
        max_id: Maximum match ID to consider (inclusive)

    Returns:
        DataFrame with matches that have NA scores
    """
    df = load_data()

    # Filter matches with NA scores and ID <= max_id
    # Note: Since load_data() uses keep_default_na=False, NA scores are stored as string "NA"
    na_matches = df[
        (df['id'] <= max_id) &
        (df['home_score'] == 'NA') &
        (df['away_score'] == 'NA')
    ].copy()

    return na_matches


def parse_prediction(prediction_text: str) -> tuple[int, int] | None:
    """
    Extract predicted score from LLM response text

    Args:
        prediction_text: Raw text output from agent

    Returns:
        Tuple of (home_score_pred, away_score_pred) or None if parsing fails
    """
    # Try multiple regex patterns to be robust
    patterns = [
        r"Predicted Score:.*?(\d+)\s*-\s*(\d+)",  # Standard format
        r"Score:.*?(\d+)\s*-\s*(\d+)",            # Abbreviated
        r"(\d+)\s*-\s*(\d+)",                      # Just the score
    ]

    for pattern in patterns:
        match = re.search(pattern, prediction_text, re.IGNORECASE)
        if match:
            home_score = int(match.group(1))
            away_score = int(match.group(2))
            return (home_score, away_score)

    return None


def predict_na_matches(max_id: int, verbose: bool = True, delay: float = 0.5) -> pd.DataFrame:
    """
    Predict all NA matches up to max_id

    Args:
        max_id: Maximum match ID to predict (inclusive)
        verbose: Print progress messages
        delay: Delay in seconds between predictions (to avoid rate limiting)

    Returns:
        DataFrame with predictions (id, home_team, away_team, home_score_pred, away_score_pred, success)
    """
    # Load matches to predict
    matches = load_na_matches(max_id)

    if len(matches) == 0:
        if verbose:
            print(f"No NA matches found with ID <= {max_id}")
        return pd.DataFrame()

    if verbose:
        print("=" * 80)
        print(f"🔮 BATCH PREDICTION MODE")
        print("=" * 80)
        print(f"Found {len(matches)} matches with NA scores (ID <= {max_id})")
        print()

    predictions = []
    success_count = 0
    error_count = 0

    for idx, (_, row) in enumerate(matches.iterrows(), 1):
        match_id = row['id']
        home_team = row['home_team']
        away_team = row['away_team']
        date = row['date']
        tournament = row['tournament']

        if verbose:
            print(f"[{idx}/{len(matches)}] Predicting: {home_team} vs {away_team} (ID: {match_id})")
            print(f"  Date: {date}, Tournament: {tournament}")

        # Construct prompt with tournament context
        prompt = f"Predict the {tournament} match between {home_team} and {away_team}."

        # Try to get prediction with retries
        prediction_text = None
        for attempt in range(3):
            try:
                prediction_text = run_agent(prompt, verbose=False)
                break
            except Exception as e:
                print(f"error: {e}")
                if attempt < 2:
                    if verbose:
                        print(f"  ⚠️  API error (attempt {attempt + 1}/3), retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    if verbose:
                        print(f"  ❌ Failed after 3 attempts: {str(e)}")
                    error_count += 1
                    predictions.append({
                        'id': match_id,
                        'date': str(date),
                        'home_team': home_team,
                        'away_team': away_team,
                        'tournament': tournament,
                        'home_score_pred': None,
                        'away_score_pred': None,
                        'success': False,
                        'error': str(e)
                    })
                    break

        if prediction_text is None:
            continue

        # Parse prediction
        parsed = parse_prediction(prediction_text)
        if parsed is None:
            if verbose:
                print(f"  ⚠️  Failed to parse prediction")
                print(f"     Response: {prediction_text[:100]}...")
            error_count += 1
            predictions.append({
                'id': match_id,
                'date': str(date),
                'home_team': home_team,
                'away_team': away_team,
                'tournament': tournament,
                'home_score_pred': None,
                'away_score_pred': None,
                'success': False,
                'error': 'Parse error'
            })
            continue

        home_score_pred, away_score_pred = parsed

        if verbose:
            print(f"  ✓ Prediction: {home_team} {home_score_pred} - {away_score_pred} {away_team}")
            print()

        success_count += 1
        predictions.append({
            'id': match_id,
            'date': str(date),
            'home_team': home_team,
            'away_team': away_team,
            'tournament': tournament,
            'home_score_pred': home_score_pred,
            'away_score_pred': away_score_pred,
            'success': True,
            'error': None
        })

        # Delay to avoid rate limiting
        if idx < len(matches):  # Don't delay after last prediction
            time.sleep(delay)

    if verbose:
        print("=" * 80)
        print(f"✓ Batch prediction complete!")
        print(f"Successful: {success_count}/{len(matches)}")
        print(f"Errors: {error_count}/{len(matches)}")
        print("=" * 80)

    return pd.DataFrame(predictions)


def save_predictions(predictions_df: pd.DataFrame, output_file: str = "predictions.csv"):
    """
    Save predictions to CSV file
    - Appends new predictions
    - Overwrites existing predictions for same match IDs (no duplicates)

    Args:
        predictions_df: DataFrame with predictions
        output_file: Output file path
    """
    from pathlib import Path

    if Path(output_file).exists():
        # Load existing predictions
        existing_df = pd.read_csv(output_file)

        # Get IDs from new predictions
        new_ids = set(predictions_df['id'])

        # Remove old predictions for the same IDs (we'll overwrite them)
        existing_df = existing_df[~existing_df['id'].isin(new_ids)]

        # Combine existing (without duplicates) and new predictions
        combined_df = pd.concat([existing_df, predictions_df], ignore_index=True)

        # Sort by ID for cleaner output
        combined_df = combined_df.sort_values('id').reset_index(drop=True)

        combined_df.to_csv(output_file, index=False)
        print(f"\n💾 Predictions saved to: {output_file}")
        print(f"   ({len(predictions_df)} new/updated, {len(existing_df)} existing kept, {len(combined_df)} total)")
    else:
        # No existing file, just save new predictions
        predictions_df.to_csv(output_file, index=False)
        print(f"\n💾 Predictions saved to: {output_file} ({len(predictions_df)} predictions)")
