import sys
from agent import run_agent
from tools import get_all_team_names
from predict_batch import predict_na_matches, save_predictions

def print_usage():
    print("Usage:")
    print("  Mode 1 - Single match prediction:")
    print("    python main.py <team1> <team2> [context]")
    print("\n  Mode 2 - Batch prediction (all NA matches up to ID):")
    print("    python main.py <max_id>")
    print("\nExamples:")
    print('  python main.py Mexico "South Africa"')
    print('  python main.py "United States" Paraguay "USA at home as co-host"')
    print('  python main.py Brazil Argentina "Group stage match"')
    print('  python main.py 44999')
    print('\nNote: Use quotes for team names with spaces')
    print('\nTo see all valid team names:')
    print('  python -c "from tools import get_all_team_names; print(\'\\n\'.join(get_all_team_names()))"')

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: Not enough arguments\n")
        print_usage()
        sys.exit(1)

    # Check if first argument is a number (batch mode)
    if len(sys.argv) == 2:
        try:
            max_id = int(sys.argv[1])
            # Batch prediction mode
            predictions_df = predict_na_matches(max_id, verbose=True)

            if len(predictions_df) > 0:
                # Save predictions
                save_predictions(predictions_df, "predictions.csv")

            sys.exit(0)
        except ValueError:
            # Not a number, treat as team name error
            print("❌ Error: Invalid usage\n")
            print_usage()
            sys.exit(1)

    # Single match prediction mode (original functionality)
    if len(sys.argv) < 3:
        print("❌ Error: Not enough arguments for single match prediction\n")
        print_usage()
        sys.exit(1)

    team1_input = sys.argv[1]
    team2_input = sys.argv[2]
    context = sys.argv[3] if len(sys.argv) > 3 else None

    # Get all valid team names
    all_teams = get_all_team_names()

    # Check if team1 is valid
    if team1_input not in all_teams:
        print(f"❌ Error: Team '{team1_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python list_teams.py')
        sys.exit(1)

    # Check if team2 is valid
    if team2_input not in all_teams:
        print(f"❌ Error: Team '{team2_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python list_teams.py')
        sys.exit(1)

    # Build the prompt
    if context:
        prompt = f"""Predict the World Cup 2026 match between {team1_input} and {team2_input}.

Context: {context}

Consider this context when making your prediction - it may affect home advantage, motivation, or other factors."""
    else:
        prompt = f"Predict the World Cup 2026 match between {team1_input} and {team2_input}."

    print("=" * 80)
    print(f"🏆 WORLD CUP 2026 PREDICTION")
    print("=" * 80)
    print(f"Match: {team1_input} vs {team2_input}")
    if context:
        print(f"Context: {context}")
    print("=" * 80)
    print("\n")

    # Run the agent
    result = run_agent(prompt, verbose=True)

    print("\n" + "=" * 80)
    print("📊 PREDICTION RESULT")
    print("=" * 80)
    print(result)
    print("=" * 80)