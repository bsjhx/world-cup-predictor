import pandas as pd
import re
import os
import sys
import time
from pathlib import Path
import argparse

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import run_agent
from tools import set_data_source


# Constants
TEST_DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = Path(__file__).parent / "predictions.csv"
ERRORS_LOG = Path(__file__).parent / "errors.log"
PARSE_ERRORS_LOG = Path(__file__).parent / "parsing_errors.log"

ACTUAL_RESULTS_FILE = TEST_DATA_DIR / "5.csv"
TEST_FILES = ["0.csv", "1.csv", "2.csv", "3.csv", "4.csv"]


def load_matches_to_predict(csv_file_path: str) -> pd.DataFrame:
    """
    Load matches from CSV file that need predictions (NA scores for World Cup 2022)

    Args:
        csv_file_path: Path to CSV file

    Returns:
        DataFrame with matches to predict (id, date, home_team, away_team, tournament)
    """
    df = pd.read_csv(csv_file_path)

    # Filter World Cup matches with NA scores
    wc_matches = df[
        (df['tournament'] == 'FIFA World Cup') &
        (pd.isna(df['home_score'])) &
        (pd.isna(df['away_score']))
    ].copy()

    return wc_matches[['id', 'date', 'home_team', 'away_team', 'tournament']]


def load_actual_results() -> pd.DataFrame:
    """
    Load actual results from 5.csv for World Cup 2022 matches

    Returns:
        DataFrame indexed by match id with actual scores
    """
    df = pd.read_csv(ACTUAL_RESULTS_FILE)

    # Filter World Cup 2022 matches
    wc_results = df[df['tournament'] == 'FIFA World Cup'].copy()

    # Set id as index for fast lookups
    wc_results = wc_results.set_index('id')

    return wc_results[['home_score', 'away_score']]


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


def evaluate_prediction(pred_home: int, pred_away: int,
                       actual_home: int, actual_away: int) -> dict:
    """
    Evaluate prediction accuracy

    Args:
        pred_home: Predicted home score
        pred_away: Predicted away score
        actual_home: Actual home score
        actual_away: Actual away score

    Returns:
        Dict with exact_match and winner_correct booleans
    """
    # Check exact match
    exact_match = (pred_home == actual_home) and (pred_away == actual_away)

    # Determine predicted result
    if pred_home > pred_away:
        pred_result = "W"
    elif pred_home == pred_away:
        pred_result = "D"
    else:
        pred_result = "L"

    # Determine actual result
    if actual_home > actual_away:
        actual_result = "W"
    elif actual_home == actual_away:
        actual_result = "D"
    else:
        actual_result = "L"

    winner_correct = (pred_result == actual_result)

    return {
        'exact_match': exact_match,
        'winner_correct': winner_correct
    }


def save_prediction(match_id: int, home_score_pred: int, away_score_pred: int,
                   exact_match: bool, winner_correct: bool, output_file: str):
    """
    Append single prediction to output CSV file

    Args:
        match_id: Match ID
        home_score_pred: Predicted home score
        away_score_pred: Predicted away score
        exact_match: Whether score was exactly correct
        winner_correct: Whether winner (W/D/L) was correct
        output_file: Path to output CSV file
    """
    # Create DataFrame for this prediction
    prediction_row = pd.DataFrame([{
        'id': match_id,
        'home_score_pred': home_score_pred,
        'away_score_pred': away_score_pred,
        'exact_match': str(exact_match).lower(),
        'winner_correct': str(winner_correct).lower()
    }])

    # Check if file exists
    file_exists = os.path.exists(output_file)

    # Append to file
    prediction_row.to_csv(
        output_file,
        mode='a',
        header=not file_exists,
        index=False
    )


def get_existing_predictions(output_file: str) -> set:
    """
    Get set of match IDs that already have predictions

    Args:
        output_file: Path to predictions CSV file

    Returns:
        Set of match IDs that have been predicted
    """
    if not os.path.exists(output_file):
        return set()

    try:
        df = pd.read_csv(output_file)
        return set(df['id'].values)
    except Exception:
        return set()


def log_error(log_file: str, message: str):
    """
    Append error message to log file

    Args:
        log_file: Path to log file
        message: Error message to log
    """
    with open(log_file, 'a') as f:
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")


def run_testing_loop():
    """
    Main orchestration function - run predictions for all test files
    """
    print("=" * 80)
    print("🧪 WORLD CUP 2022 PREDICTION TESTING")
    print("=" * 80)
    print()

    # Load actual results once
    print("Loading actual results from 5.csv...")
    actual_results = load_actual_results()
    print(f"✓ Loaded {len(actual_results)} World Cup 2022 match results")
    print()

    # Get existing predictions to allow resuming
    existing_predictions = get_existing_predictions(OUTPUT_FILE)
    if existing_predictions:
        print(f"ℹ️  Found {len(existing_predictions)} existing predictions - will skip those")
        print()

    total_predictions = 0
    total_skipped = 0
    total_errors = 0

    # Process each test file
    for test_file in TEST_FILES:
        file_path = TEST_DATA_DIR / test_file
        print(f"Processing {test_file}...")

        # Set data source for tools to use this test file
        set_data_source(str(file_path))
        print(f"✓ Set data source to {test_file}")

        # Load matches to predict
        matches = load_matches_to_predict(file_path)
        print(f"Found {len(matches)} matches with NA scores")
        print()

        file_predictions = 0
        file_skipped = 0
        file_errors = 0

        # Process each match
        for _, row in matches.iterrows():
            match_id = row['id']
            home_team = row['home_team']
            away_team = row['away_team']

            # Skip if already predicted
            if match_id in existing_predictions:
                file_skipped += 1
                continue

            # Check if actual result exists
            if match_id not in actual_results.index:
                error_msg = f"Match {match_id} ({home_team} vs {away_team}) - No actual result found in 5.csv"
                print(f"⚠️  {error_msg}")
                log_error(ERRORS_LOG, error_msg)
                file_errors += 1
                continue

            # Construct prompt
            prompt = f"Predict the World Cup 2022 match between {home_team} and {away_team}."

            # Try to get prediction with retries
            prediction_text = None
            for attempt in range(3):
                try:
                    prediction_text = run_agent(prompt, verbose=False)
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"⚠️  API error (attempt {attempt + 1}/3), retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        error_msg = f"Match {match_id} ({home_team} vs {away_team}) - API error: {str(e)}"
                        print(f"❌ {error_msg}")
                        log_error(ERRORS_LOG, error_msg)
                        file_errors += 1
                        continue

            if prediction_text is None:
                continue

            # Parse prediction
            parsed = parse_prediction(prediction_text)
            if parsed is None:
                error_msg = f"Match {match_id} ({home_team} vs {away_team}) - Failed to parse prediction"
                print(f"⚠️  {error_msg}")
                log_error(PARSE_ERRORS_LOG, f"{error_msg}\nPrediction text:\n{prediction_text}\n{'-'*40}\n")
                file_errors += 1
                continue

            home_score_pred, away_score_pred = parsed

            # Get actual result
            actual_home = int(actual_results.loc[match_id, 'home_score'])
            actual_away = int(actual_results.loc[match_id, 'away_score'])

            # Evaluate prediction
            evaluation = evaluate_prediction(
                home_score_pred, away_score_pred,
                actual_home, actual_away
            )

            # Save prediction
            save_prediction(
                match_id, home_score_pred, away_score_pred,
                evaluation['exact_match'], evaluation['winner_correct'],
                OUTPUT_FILE
            )

            # Print progress
            exact_icon = "✓" if evaluation['exact_match'] else "○"
            winner_icon = "✓" if evaluation['winner_correct'] else "✗"
            print(f"{exact_icon} Match {match_id}: {home_team} vs {away_team} - "
                  f"Predicted: {home_score_pred}-{away_score_pred}, "
                  f"Actual: {actual_home}-{actual_away} "
                  f"[Exact: {exact_icon}, Winner: {winner_icon}]")

            file_predictions += 1

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        print()
        print(f"Completed {test_file}: {file_predictions} predictions made, "
              f"{file_skipped} skipped, {file_errors} errors")
        print("-" * 80)
        print()

        total_predictions += file_predictions
        total_skipped += file_skipped
        total_errors += file_errors

    print("=" * 80)
    print(f"✓ Testing complete!")
    print(f"Total predictions: {total_predictions}")
    print(f"Skipped (already done): {total_skipped}")
    print(f"Errors: {total_errors}")
    print("=" * 80)
    print()

    # Print final summary
    print_final_summary()


def print_final_summary():
    """
    Print aggregate statistics from all predictions
    """
    if not os.path.exists(OUTPUT_FILE):
        print("No predictions file found!")
        return

    # Load predictions
    df = pd.read_csv(OUTPUT_FILE)

    if len(df) == 0:
        print("No predictions to summarize!")
        return

    # Calculate metrics (pandas auto-converts 'true'/'false' strings to booleans)
    total = len(df)
    exact_matches = (df['exact_match'] == True).sum()
    winner_correct = (df['winner_correct'] == True).sum()

    exact_pct = (exact_matches / total * 100) if total > 0 else 0
    winner_pct = (winner_correct / total * 100) if total > 0 else 0

    print("=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Predictions: {total}")
    print(f"Exact Score Matches: {exact_matches} ({exact_pct:.2f}%)")
    print(f"Winner Correct: {winner_correct} ({winner_pct:.2f}%)")
    print("=" * 80)

def print_results():
    # Load predictions
    df = pd.read_csv(OUTPUT_FILE)

    if len(df) == 0:
        print("No predictions to summarize!")
        return

    # Calculate metrics (pandas auto-converts 'true'/'false' strings to booleans)
    total = len(df)
    exact_matches = (df['exact_match'] == True).sum()
    winner_correct = (df['winner_correct'] == True).sum()

    exact_pct = (exact_matches / total * 100) if total > 0 else 0
    winner_pct = (winner_correct / total * 100) if total > 0 else 0

    print("=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Predictions: {total}")
    print(f"Exact Score Matches: {exact_matches} ({exact_pct:.2f}%)")
    print(f"Winner Correct: {winner_correct} ({winner_pct:.2f}%)")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-results", action="store_true")
    args = parser.parse_args()

    if args.only_results:
        print_results()
    else:
        run_testing_loop()

if __name__ == "__main__":
    main()