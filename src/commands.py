import sys
from src.agent import run_agent
from src.tools import get_all_team_names
from src.predict_batch import predict_na_matches, save_predictions

def cmd_predict(args):
    """Handle the 'predict' command - single match prediction"""
    team1_input = args.team1
    team2_input = args.team2
    context = args.context

    # Get all valid team names
    all_teams = get_all_team_names()

    # Validate team1
    if team1_input not in all_teams:
        print(f"❌ Error: Team '{team1_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python src/main.py list-teams')
        sys.exit(1)

    # Validate team2
    if team2_input not in all_teams:
        print(f"❌ Error: Team '{team2_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python src/main.py list-teams')
        sys.exit(1)

    # Build the prompt
    if context:
        prompt = f"""Predict the World Cup 2026 match between {team1_input} and {team2_input}.

Context: {context}

Consider this context when making your prediction - it may affect home advantage, motivation, or other factors."""
    else:
        prompt = f"Predict the World Cup 2026 match between {team1_input} and {team2_input}."

    # Display header
    print("=" * 80)
    print(f"🏆 WORLD CUP 2026 PREDICTION")
    print("=" * 80)
    print(f"Match: {team1_input} vs {team2_input}")
    if context:
        print(f"Context: {context}")
    print("=" * 80)
    print("\n")

    # Run the agent
    result = run_agent(prompt, verbose=not args.quiet)

    # Display result
    print("\n" + "=" * 80)
    print("📊 PREDICTION RESULT")
    print("=" * 80)
    print(result)
    print("=" * 80)


def cmd_batch(args):
    """Handle the 'batch' command - batch predictions up to max_id"""
    max_id = args.max_id
    output_file = args.output or "predictions.csv"
    verbose = not args.quiet

    # Run batch predictions
    predictions_df = predict_na_matches(max_id, verbose=verbose)

    if len(predictions_df) > 0:
        save_predictions(predictions_df, output_file)
    else:
        print(f"No matches found with ID <= {max_id}")


def cmd_list_teams(args):
    """Handle the 'list-teams' command"""
    teams = get_all_team_names()

    print("=" * 80)
    print(f"📋 ALL VALID TEAM NAMES ({len(teams)} teams)")
    print("=" * 80)
    print()

    for idx, team in enumerate(teams, 1):
        # Add quotes if team name has spaces
        display_name = f'"{team}"' if ' ' in team else team
        print(f"{idx:3}. {display_name}")

    print()
    print("=" * 80)
    print("💡 Use these exact names (with quotes if they contain spaces)")
    print("   Example: python src/main.py predict \"United States\" Mexico")
    print("=" * 80)
